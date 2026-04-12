import os
import time
import tempfile

def benchmark_disk_latency(target_dir: str) -> float:
    """
    Realiza una heurística de perfilado I/O escribiendo un pequeñito
    bloque de datos de forma transaccional usando os.fsync().
    
    Devuelve el tiempo (latencia) de escritura en segundos.
    """
    # 2 MB sample size to ensure we bypass some naive caches and hit disk.
    sample_data = os.urandom(2 * 1024 * 1024) 
    
    # Nos aseguramos de escribir en el directorio destino (el del proyecto git)
    # y no en el disco de sistema (C: / /tmp) a menos que este sea el objetivo.
    # Así perfilamos exactamente el disco que va a recibir el estrés.
    latency = 0.0
    try:
        start_time = time.time()
        
        # O_SYNC o fsync nativo nos aseguran escribir directo al metal
        with tempfile.NamedTemporaryFile(dir=target_dir, delete=False) as f:
            temp_name = f.name
            f.write(sample_data)
            f.flush()
            os.fsync(f.fileno())
            
        latency = time.time() - start_time
    except Exception:
        # En caso de no tener permisos para probar, asumimos un perfil conservador
        latency = 999.0
    finally:
        # Limpieza
        try:
            if 'temp_name' in locals() and os.path.exists(temp_name):
                os.remove(temp_name)
        except Exception:
            pass
            
    return latency

def calculate_optimal_workers(target_dir: str, requested_workers: int = 0) -> int:
    """
    Determina la cantidad óptima de hilos para ejecución concurrente de Git.
    Si requested_workers > 0, lo devuelve (con un límite máximo seguro de 50).
    Si requested_workers == 0, hace un perfilado I/O.
    """
    MAX_WORKERS_ABSOLUTE = 50
    
    if requested_workers > 0:
        return min(requested_workers, MAX_WORKERS_ABSOLUTE)
        
    latency = benchmark_disk_latency(target_dir)
    cores = os.cpu_count() or 4
    
    if latency > 0.15:
        # Muy lento (> 150ms). Red, HDD viejo, o sobrecargado.
        optimal = max(4, cores)
    elif latency > 0.05:
        # Moderado-Lento (50-150ms). HDD estándar.
        optimal = max(6, cores * 2) 
    else:
        # Rápido (< 50ms). NVMe, SSD, o caché en RAM.
        optimal = cores * 4
        
    return min(optimal, MAX_WORKERS_ABSOLUTE)

