import pickle

class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == 'ctgan.synthesizers.ctgan' and name == 'CTGANSynthesizer':
            from ctgan import CTGAN
            return CTGAN
        return super().find_class(module, name)

def load_old_pickle(file_path):
    with open(file_path, "rb") as f:
        return SafeUnpickler(f).load()