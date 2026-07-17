from movie.prop_library import generate_props, load_props, save_prop
class PropLibraryService:
    load = staticmethod(load_props)
    generate = staticmethod(generate_props)
    save = staticmethod(save_prop)
