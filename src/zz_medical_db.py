import db
import services_specialist

data = {
    "collegiateNumber": "133-666",
    "firstName": "Marta",
    "secondName": "Pérez",
    "birthDate": "1985-05-20",
    "email": "marta@medico.com",
    "password": "soymartaa",
    "countryCode": "ES",
    "centerName": "CAP Les Corts",
    "centerCity": "Barcelona"
}

coll_number = data["collegiateNumber"]

services_specialist.handle_registration(data)