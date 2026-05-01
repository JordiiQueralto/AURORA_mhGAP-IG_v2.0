import db

def handle_registration(data):
    coll_number = str(data['collegiateNumber']).replace(" ", "")
    
    # 1. Comprobamos si ya existe
    is_registered = db.is_registered(coll_number)
    
    if is_registered:
        return True
    else:
        # Si es nuevo, registramos todos los datos
        db.register_med(coll_number, data)
        return False
    

def save_profile_update(coll_number, profile_data):
    """
    Guarda la información actualizada del perfil del usuario en la BD.
    """
    coll_number = str(coll_number).replace(" ", "")
    db.add_med_info(coll_number, "PROFILE", profile_data)
    return


def get_profile_data(coll_number):
    """
    Recupera la información de 'Mi círculo' del perfil del usuario en la BD.
    """
    coll_number = str(coll_number).replace(" ", "")
    contacts = db.get_user_info(coll_number, "CIRCLE", "contacts") or {}
    medicalCenter = db.get_user_info(coll_number, "CIRCLE", "medicalCenter") or {}
    privacy = db.get_user_info(coll_number, "CIRCLE", "privacy") or {}
    
    profile_data = {
            "contacts": contacts,
            "medicalCenter": medicalCenter,
            "privacy": privacy
            }
    
    return profile_data