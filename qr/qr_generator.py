import os
import qrcode


def generate_qr(verification_url, filename):

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    image = qr.make_image()

    image.save(filename)

    return filename