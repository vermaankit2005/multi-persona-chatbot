from db import SessionLocal
from model import Personas


def db_get_persona(persona_key, db_session) -> Personas:
    return db_session.query(Personas).filter(Personas.key == persona_key).first()


def db_get_all_personas(db_session) -> list[Personas]:
    return db_session.query(Personas).all()


def __create_persona(persona: Personas, db_session):
    db_session.add(persona)
    db_session.commit()


def __delete_persona(persona_key: str, db_session):
    persona = db_session.query(Personas).filter(Personas.key == persona_key).first()
    if persona:
        db_session.delete(persona)
        db_session.commit()


# TODO: Test function to create personas in the database if they don't exist - THIS IS TEMPORARY AND SHOULD BE PART OF A SEED SCRIPT OR MIGRATION.
if __name__ == "__main__":
    personas = [
        Personas(key="grumpy_pirate", name="Grumpy Pirate",
                 system_prompt="You are a grumpy pirate assistant, who is always complaining and grumbling."),
        Personas(key="drunk_man", name="Drunk Man",
                 system_prompt="You are a drunk man assistant, who is always tipsy and slurring."),
        Personas(key="donald_duck", name="Donald Duck",
                 system_prompt="You are a humorous duck assistant, who speaks like Donald Duck."),
        Personas(key="sarcastic_robot", name="Sarcastic Robot",
                 system_prompt="You are a sarcastic robot assistant, who always responds with sarcasm in robotic tones.")
    ]
    db = SessionLocal()

    persons_in_db = db.query(Personas).all()
    for persona in personas:
        if persona.key not in [p.key for p in persons_in_db]:
            __create_persona(db, persona)
