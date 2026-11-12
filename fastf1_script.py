import pickle
import pandas as pd
import os

class CustomUnpickler(pickle.Unpickler):
    """Gestisce la compatibilità dei moduli NumPy/Pandas tra versioni differenti."""
    def find_class(self, module, name):
        if 'numpy._core' in module:
            module = module.replace('numpy._core', 'numpy.core')
        return super().find_class(module, name)

def load_ff1pkl(filepath):
    with open(filepath, 'rb') as f:
        content = CustomUnpickler(f).load()
        # I file FastF1 contengono solitamente un dizionario con la chiave 'data'
        if isinstance(content, dict) and 'data' in content:
            return content['data']
        return content

def convert_to_celonis_csv():
    files = [f for f in os.listdir('.') if f.endswith('.ff1pkl')]
    
    for file_path in files:
        base_name = os.path.splitext(file_path)[0]
        data = load_ff1pkl(file_path)
        
        df = None
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, dict):
            try:
                df = pd.DataFrame(data)
            except Exception:
                # Se è un dizionario annidato (es. driver_info)
                df = pd.DataFrame.from_dict(data, orient='index')
        
        if df is not None:
            # Gestione formati per Celonis: converti i Timedelta di FastF1 in secondi o ISO string
            for col in df.columns:
                if pd.api.types.is_timedelta64_dtype(df[col]):
                    df[col] = df[col].dt.total_seconds()
            
            output_csv = f"{base_name}.csv"
            df.to_csv(output_csv, index=False)
            print(f"✅ Creato: {output_csv}")

if __name__ == "__main__":
    convert_to_celonis_csv()