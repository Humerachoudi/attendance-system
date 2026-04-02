import qrcode
import os

def generate_qr(teacher_id: int):
    """Generate permanent QR code for Smart Attendance"""
    qr_text = f"TEACHER-{teacher_id}"  # ✅ Same every day

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_M
    )

    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_dir = "backend/static/qr_codes"
    os.makedirs(qr_dir, exist_ok=True)

    qr_path = os.path.join(qr_dir, f"qr_{teacher_id}.png")  # no date
    qr_img.save(qr_path)

    return qr_path, qr_text
