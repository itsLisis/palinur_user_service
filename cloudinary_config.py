import cloudinary
import cloudinary.uploader
from config import settings

# Configurar Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

def upload_image(file_content, folder="profile_images"):
    """
    Sube una imagen a Cloudinary y retorna la URL pública.
    
    Args:
        file_content: Contenido del archivo (bytes)
        folder: Carpeta en Cloudinary donde se guardará
        
    Returns:
        str: URL pública de la imagen subida
    """
    try:
        upload_result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            resource_type="image"
        )
        return upload_result.get("secure_url")
    except Exception as e:
        raise Exception(f"Error uploading image to Cloudinary: {str(e)}")

def delete_image(public_id):
    """
    Elimina una imagen de Cloudinary.
    
    Args:
        public_id: ID público de la imagen en Cloudinary
        
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        raise Exception(f"Error deleting image from Cloudinary: {str(e)}")
