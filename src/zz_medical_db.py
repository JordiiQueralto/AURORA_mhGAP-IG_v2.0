import db
import main_api_sp

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

main_api_sp.handle_registration(data)