from app import app, db
from models import Toy

def add_toys():
    with app.app_context():
        # Primero, eliminar todos los juguetes existentes
        Toy.query.delete()
        
        # Lista de juguetes con sus detalles
        toys = [
            # Niña
            {"name": "Pulseras Mágicas", "description": "Pulseras con lentejuelas reversibles.", "category": "Niña", "price": 25.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Juego de Té", "description": "Set de juguete para jugar a la hora del té.", "category": "Niña", "price": 25.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Juego de Cocina", "description": "Set de juguete con utensilios de cocina.", "category": "Niña", "price": 28.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Burbujeros", "description": "Frascos con líquido para hacer burbujas.", "category": "Niña", "price": 7.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Brillo Labial", "description": "Brillo para labios.", "category": "Niña", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rompecabezas Frozen", "description": "Rompecabezas con imagen de Frozen.", "category": "Niña", "price": 28.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Libro Colorear (Pony/Cisne)", "description": "Libro para colorear con lápices.", "category": "Niña", "price": 8.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Cartera Cola de Sirena", "description": "Cartera con lentejuelas.", "category": "Niña", "price": 20.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Accesorios para Pulseras", "description": "Set para crear pulseras.", "category": "Niña", "price": 50.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Vincha de Reina", "description": "Vincha con diseño de corona.", "category": "Niña", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Burbujeador para Niñas", "description": "Burbujeador con diseños para niñas.", "category": "Niña", "price": 10.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Gorro Divertido", "description": "Gorro con orejas movibles.", "category": "Niña", "price": 65.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rompecabezas Princesas", "description": "Rompecabezas con princesas Disney.", "category": "Niña", "price": 28.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Slime con Unicornio", "description": "Slime con figura de unicornio.", "category": "Niña", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Kit Bolso para Colorear", "description": "Kit para colorear un bolso.", "category": "Niña", "price": 50.0, "image_url": "/static/images/toys/default_toy.png"},

            # Niño
            {"name": "Mangas Tattoo", "description": "Mangas con diseños de tatuajes.", "category": "Niño", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Stickers Reflectivos Emojis", "description": "Stickers con emojis reflectivos.", "category": "Niño", "price": 14.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Bigote Pirata", "description": "Bigote postizo de pirata.", "category": "Niño", "price": 12.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Clavo Falso en el Dedo", "description": "Broma de clavo en el dedo.", "category": "Niño", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Hormigas Falsas", "description": "Hormigas de juguete para bromas.", "category": "Niño", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Herramientas de Construcción", "description": "Set de herramientas de juguete.", "category": "Niño", "price": 30.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Gorra Aloha", "description": "Gorra con logo de Aloha.", "category": "Niño", "price": 40.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Carro Hot Wheels", "description": "Carro Hot Wheels.", "category": "Niño", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rompecabezas de Carro", "description": "Rompecabezas de un carro.", "category": "Niño", "price": 20.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Pistolas de Agua Dinosaurio", "description": "Pistolas de agua con forma de dinosaurio.", "category": "Niño", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Yates con Llantas", "description": "Yates de juguete con ruedas.", "category": "Niño", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Carritos de Colores", "description": "Carritos de carreras.", "category": "Niño", "price": 6.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Muñeco Pegajoso", "description": "Muñeco que se pega a las paredes.", "category": "Niño", "price": 2.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rompecabezas Spiderman", "description": "Rompecabezas de Spiderman.", "category": "Niño", "price": 28.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Libro Colorear Superhéroes", "description": "Libro para colorear de superhéroes.", "category": "Niño", "price": 8.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Libro para colorear Mario Bros", "description": "Libro para colorear de Mario Bros.", "category": "Niño", "price": 8.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Casco de Construcción", "description": "Casco de juguete de constructor.", "category": "Niño", "price": 48.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Raqueta de Playa con Pelota", "description": "Raqueta y pelota de playa.", "category": "Niño", "price": 48.0, "image_url": "/static/images/toys/default_toy.png"},

            # Mixto
            {"name": "Pegatina", "description": "Lámina con pegatinas.", "category": "Mixta", "price": 3.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Jacks", "description": "Juego tradicional con pelota y piezas.", "category": "Mixta", "price": 5.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Mini Resortes", "description": "Pequeños resortes de plástico.", "category": "Mixta", "price": 4.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rompecabezas", "description": "Juego de ingenio para armar figuras.", "category": "Mixta", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Juguetes Voladores Platillo", "description": "Juguetes que se lanzan al aire.", "category": "Mixta", "price": 10.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Salta Soga con Contador", "description": "Cuerda para saltar con contador.", "category": "Mixta", "price": 20.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Juego de Aros con Agua", "description": "Juego de lanzar aros a una base con agua.", "category": "Mixta", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Pizarra Magnética c/ Alfabeto", "description": "Pizarra magnética con letras y marcador.", "category": "Mixta", "price": 45.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Pelotas Espuma Emojis", "description": "Pelotas de espuma con emojis.", "category": "Mixta", "price": 18.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Rubik", "description": "Cubo de Rubik.", "category": "Mixta", "price": 17.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Yoyo Clásico", "description": "Yoyo tradicional.", "category": "Mixta", "price": 18.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Yoyo de Goma", "description": "Yoyo de goma con pelo largo.", "category": "Mixta", "price": 2.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Yoyo en forma de Balón", "description": "Yoyo con forma de balón.", "category": "Mixta", "price": 4.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Mini Resortes Balón", "description": "Mini resortes con forma de balón.", "category": "Mixta", "price": 4.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Slime con Astronauta", "description": "Slime con astronauta dentro.", "category": "Mixta", "price": 15.0, "image_url": "/static/images/toys/default_toy.png"},
            {"name": "Walkie Talkies", "description": "Par de walkie talkies.", "category": "Mixta", "price": 65.0, "image_url": "/static/images/toys/default_toy.png"},
        ]

        # Agregar cada juguete a la base de datos
        for toy_data in toys:
            toy = Toy(**toy_data)
            db.session.add(toy)
        
        try:
            db.session.commit()
            print("✅ Juguetes agregados exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al agregar juguetes: {e}")

if __name__ == '__main__':
    add_toys()
