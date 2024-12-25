from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import numpy as np
from sklearn.cluster import KMeans
import threading
import time
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

app = Flask(__name__)
CORS(app)


imagekit = ImageKit(
    private_key='',# contoh private_key='public_QF2313242',
    public_key='', # contoh public_key='public_QFy5ti1212',
    url_endpoint='' #contoh https://ik.imagekit.io/ycczrhq
)

MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3 mb
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def get_dominant_color(image_bytes, num_colors=1):
    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert('RGB')
    image_array = np.array(image)
    reshaped_image = image_array.reshape(-1, 3)
    
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(reshaped_image)
    
    dominant_colors = kmeans.cluster_centers_
    hex_colors = ['#{:02x}{:02x}{:02x}'.format(int(color[0]), int(color[1]), int(color[2])) 
                 for color in dominant_colors]
    
    return hex_colors[0] if hex_colors else None

def delete_imagekit_file(file_id):
    time.sleep(5)  # langsung hapus 5 detik abis uplode
    try:
        imagekit.delete_file(file_id)
        print(f"File dengan ID {file_id} berhasil dihapus dari ImageKit")
    except Exception as e:
        print(f"Error saat menghapus file: {str(e)}")

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if len(file.read()) > MAX_CONTENT_LENGTH:
        return jsonify({"error": "File is too large, maximum size is 3MB"}), 400
    
    file.seek(0)

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in allowed_extensions:
        return jsonify({"error": "File type not allowed"}), 400

    try:
        file_bytes = file.read()
        
        upload_options = UploadFileRequestOptions(
            use_unique_file_name=True,
            tags=['auto-delete']
        )
        
        upload_response = imagekit.upload_file(
            file=file_bytes,
            file_name=file.filename,
            options=upload_options
        )

        hex_color = get_dominant_color(file_bytes)

        threading.Thread(
            target=delete_imagekit_file,
            args=(upload_response.file_id,)
        ).start()
        
        return jsonify({
            "hex_color": hex_color,
            "filename": file.filename,
            "imagekit_url": upload_response.url,
            "file_id": upload_response.file_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)