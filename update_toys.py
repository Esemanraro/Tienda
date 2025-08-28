from app import app, db
from models import Toy

toys_data = [
    # Juguetes de Niña
    {
        "name": "PEGATINA PARA NIÑA",
        "price": 12.00,
        "description": "Pegatinas decorativas para niñas.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "PULSERAS MÁGICAS",
        "price": 25.00,
        "description": "Pulseras con brillo reversible para niñas.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "JUEGO DE TÉ",
        "price": 25.00,
        "description": "Juego de té para compartir con amigos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "JUEGO DE COCINA",
        "price": 25.00,
        "description": "Juego de cocina para jugar con amigos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "BRILLO LABIAL",
        "price": 5.00,
        "description": "Labiales de brillo con aroma.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "ROMPECABEZA FROZEN",
        "price": 28.00,
        "description": "Rompecabeza de 48 piezas de la princesa Ana.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "LIBRO DE COLOREAR PONNY",
        "price": 8.00,
        "description": "Libro de colorear con 12 y 8 lapiceros incluidos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "LIBRO DE COLOREAR CISNE",
        "price": 8.00,
        "description": "Libro de colorear con 8 y 12 lapiceros incluidos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "JACKS",
        "price": 8.00,
        "description": "Juego clásico de jacks coloridos para jugar con amigos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "CARTERA EN FORMA DE COLA DE SIRENA",
        "price": 50.00,
        "description": "Cartera brillosa de lentejuelas con forma de cola de sirena.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "ACCESORIOS DE BISUTERÍA PARA CREAR PULSERAS",
        "price": 10.00,
        "description": "Kit para armar pulseras con accesorios de bisutería.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "VINCHA DE REINA",
        "price": 20.00,
        "description": "Vinchas de lentejuelas con forma de corona de princesa.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "GORRO DIVERTIDO COLORIDO",
        "price": 45.00,
        "description": "Gorro con orejas que se mueven.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "PIZARRA MAGNÉTICA CON ALFABETO",
        "price": 15.00,
        "description": "Pizarra magnética con alfabeto y marcador incluido.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },
    {
        "name": "SLIME CON UNICORNIO",
        "price": 20.00,
        "description": "Slime con un muñeco de unicornio dentro.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niña"
    },

    # Juguetes de Niño
    {
        "name": "MANGAS TATTOO",
        "price": 15.00,
        "description": "Mangas de tatuaje para niños.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "STICKERS REFLECTIVOS DE EMOJIS",
        "price": 12.00,
        "description": "Stickers reflectivos para mochilas.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "BIGOTE PIRATA",
        "price": 14.00,
        "description": "Barba y bigote estilo pirata para niños.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "CLAVO FALSO EN EL DEDO",
        "price": 5.00,
        "description": "Juego de broma que parece un clavo en el dedo.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "HORMIGAS FALSAS",
        "price": 5.00,
        "description": "Juguetes de hormigas falsas para diversión.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "HERRAMIENTAS DE CONSTRUCCIÓN DE JUGUETE",
        "price": 40.00,
        "description": "Herramientas de construcción para niños mayores de 3 años.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "GORRA DE ALOHA BLANCA CON NEGRO",
        "price": 30.00,
        "description": "Gorras unisex de Aloha en color blanco y negro.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },
    {
        "name": "CARRO HOT WHEELS",
        "price": 7.00,
        "description": "Carro rojo de la serie Hot Wheels.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Niño"
    },

    # Juguetes Mixtos
    {
        "name": "BURBUJEROS",
        "price": 17.00,
        "description": "Burbujeros con forma de oso, colores azul y verde.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "MINI RESORTES",
        "price": 10.00,
        "description": "Mini resortes en colores vivos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "ROMPECOCO",
        "price": 15.00,
        "description": "Juego didáctico de habilidad mental.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "JUGUETES VOLADORES DE PLATILLO",
        "price": 4.00,
        "description": "Juguetes voladores de presión manual para niños y niñas.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "SALTA SOGA CON CONTADOR",
        "price": 20.00,
        "description": "Soga para saltar con contador de saltos.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "PELOTAS DE ESPUMA CON EMOJIS",
        "price": 18.00,
        "description": "Pelotas antiestrés de espuma con emojis.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    },
    {
        "name": "KIT DE BOLSO PARA COLOREAR",
        "price": 50.00,
        "description": "Bolso de colorear con dibujos para niños.",
        "image_url": "/static/images/toys/default_toy.png",
        "category": "Mixto"
    }
]

def update_toys():
    with app.app_context():
        try:
            # Eliminar todos los juguetes existentes
            print("Eliminando juguetes existentes...")
            Toy.query.delete()
            
            # Agregar los nuevos juguetes con categorías
            print("Agregando nuevos juguetes...")
            for toy_data in toys_data:
                toy = Toy(
                    name=toy_data['name'],
                    price=toy_data['price'],
                    description=toy_data['description'],
                    image_url=toy_data['image_url'],
                    category=toy_data['category']
                )
                db.session.add(toy)
            
            # Guardar cambios
            db.session.commit()
            print("✨ Catálogo actualizado exitosamente!")
            
            # Mostrar resumen
            print("\nResumen del catálogo:")
            print(f"Total de juguetes: {Toy.query.count()}")
            for category in ['Niña', 'Niño', 'Mixto']:
                count = Toy.query.filter_by(category=category).count()
                print(f"Juguetes de {category}: {count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al actualizar el catálogo: {str(e)}")

if __name__ == '__main__':
    update_toys()
