
import base64
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from cryptography.exceptions import InvalidTag
from starlette.responses import Response

from quantum.bb84 import run_bb84
from database import get_db_connection
from encryption.aes import encrypt_file, decrypt_file


# ==========================================
# 1. APPLICATION AND SESSION STATE
# ==========================================

app = FastAPI(
    title="Q-Secure API",
    description="BB84 Quantum Key Distribution and Secure File Transfer",
    version="1.0"
)

# Educational demo: retain the latest secure key in backend memory.
# It is lost when the backend restarts.
latest_shared_key = None
latest_exchange_id = None


# ==========================================
# 2. CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Nonce"]
)


# ==========================================
# 3. REQUEST MODEL
# ==========================================

class BB84Request(BaseModel):
    n: int = Field(default=1000, ge=100, le=10000)
    eve_present: bool = False


# ==========================================
# 4. HOME API
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Welcome to Q-Secure API",
        "status": "Running"
    }


# ==========================================
# 5. HEALTH CHECK API
# ==========================================

@app.get("/api/health")
def health():
    return {
        "status": "Backend is running"
    }


# ==========================================
# 6. BB84 SIMULATION API
# ==========================================

@app.post("/api/bb84")
def simulate_bb84(request: BB84Request):

    global latest_shared_key, latest_exchange_id

    result = run_bb84(
        n=request.n,
        eve_present=request.eve_present
    )

    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    # Keep the key on the backend, never return it to React.
    if result["security_status"] == "SECURE":
        latest_shared_key = result["shared_key"]
    else:
        latest_shared_key = None

    connection = get_db_connection()
    db_saved = False
    latest_exchange_id = None

    if connection:
        try:
            cursor = connection.cursor()

            query = """
                INSERT INTO key_exchanges
                (
                    total_qubits,
                    matching_bases,
                    qber,
                    security_status
                )
                VALUES (%s, %s, %s, %s)
            """

            values = (
                result["total_qubits"],
                result["matching_bases"],
                result["qber"],
                result["security_status"]
            )

            cursor.execute(query, values)
            connection.commit()

            latest_exchange_id = cursor.lastrowid
            result["exchange_id"] = latest_exchange_id
            db_saved = True

            cursor.close()

        except Exception as e:
            connection.rollback()
            print("Database insertion error:", e)

        finally:
            connection.close()

    result["db_saved"] = db_saved

    # Do not expose the shared key in the API response.
    result.pop("shared_key", None)

    return result


# ==========================================
# 7. EXCHANGE HISTORY API
# ==========================================

@app.get("/api/history")
def get_exchange_history():

    connection = get_db_connection()

    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                exchange_id,
                total_qubits,
                matching_bases,
                qber,
                security_status,
                created_at
            FROM key_exchanges
            ORDER BY exchange_id DESC
        """)

        records = cursor.fetchall()
        cursor.close()

        return {"history": records}

    except Exception as e:
        print("History retrieval error:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve exchange history"
        )

    finally:
        connection.close()


# ==========================================
# 8. AES FILE ENCRYPTION API
# ==========================================

@app.post("/api/files/encrypt")
async def encrypt_uploaded_file(
    file: UploadFile = File(...)
):

    if not latest_shared_key:
        raise HTTPException(
            status_code=400,
            detail="No secure BB84 key available. Run BB84 successfully first."
        )

    try:
        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        encrypted_result = encrypt_file(
            file_data,
            latest_shared_key
        )

        encrypted_data = encrypted_result["encrypted_data"]
        nonce = encrypted_result["nonce"]

        # Save file-transfer metadata in MySQL.
        connection = get_db_connection()

        if connection and latest_exchange_id is not None:
            try:
                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO file_transfers
                    (filename, exchange_id)
                    VALUES (%s, %s)
                """, (
                    file.filename or "uploaded_file",
                    latest_exchange_id
                ))

                connection.commit()
                cursor.close()

            except Exception as e:
                connection.rollback()
                print("File history insertion error:", e)

            finally:
                connection.close()

        return Response(
            content=encrypted_data,
            media_type="application/octet-stream",
            headers={
                "X-Nonce": base64.b64encode(nonce).decode("utf-8"),
                "Content-Disposition":
                    f'attachment; filename="{quote("encrypted_" + (file.filename or "file"))}"'
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        print("Encryption error:", e)

        raise HTTPException(
            status_code=500,
            detail="File encryption failed."
        )

    finally:
        await file.close()


# ==========================================
# 9. AES FILE DECRYPTION API
# ==========================================

@app.post("/api/files/decrypt")
async def decrypt_uploaded_file(
    file: UploadFile = File(...),
    nonce: str = Form(...)
):

    if not latest_shared_key:
        raise HTTPException(
            status_code=400,
            detail="No secure BB84 key available. Run BB84 successfully first."
        )

    try:
        encrypted_data = await file.read()

        try:
            nonce_bytes = base64.b64decode(
                nonce,
                validate=True
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid nonce format."
            )

        if len(nonce_bytes) != 12:
            raise HTTPException(
                status_code=400,
                detail="Invalid AES-GCM nonce length."
            )

        decrypted_data = decrypt_file(
            encrypted_data,
            nonce_bytes,
            latest_shared_key
        )

        original_filename = file.filename or "decrypted_file"

        if original_filename.startswith("encrypted_"):
            original_filename = original_filename[len("encrypted_"):]

        return Response(
            content=decrypted_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{quote("decrypted_" + original_filename)}"'
            }
        )

    except InvalidTag:
        raise HTTPException(
            status_code=400,
            detail="Decryption failed. The key or encrypted file is incorrect."
        )

    except HTTPException:
        raise

    except Exception as e:
        print("Decryption error:", e)

        raise HTTPException(
            status_code=500,
            detail="File decryption failed."
        )

    finally:
        await file.close()

# ==========================================
# 10. FILE TRANSFER HISTORY API
# ==========================================

@app.get("/api/files/history")
def get_file_transfer_history():

    connection = get_db_connection()

    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                file_id,
                filename,
                exchange_id,
                created_at
            FROM file_transfers
            ORDER BY file_id DESC
        """)

        records = cursor.fetchall()

        cursor.close()

        return {
            "file_history": records
        }

    except Exception as e:
        print("File history retrieval error:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve file transfer history"
        )

    finally:
        connection.close()
