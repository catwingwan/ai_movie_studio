from movie.location_bible import generate_location_bibles, load_location_bibles, save_location_bible
class LocationBibleService:
    load = staticmethod(load_location_bibles)
    generate = staticmethod(generate_location_bibles)
    save = staticmethod(save_location_bible)
