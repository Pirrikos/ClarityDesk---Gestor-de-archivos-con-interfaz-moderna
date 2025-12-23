"""
IconService - Windows native icon provider for files.

Provides native Windows icons for file paths with caching per extension.
Supports batch icon generation using QThread workers.

This service provides RAW Windows icons (QIcon/QPixmap) without any
visual normalization, preview generation, or fallbacks. For previews with
normalization, use IconRenderService.
"""

import os
import time
from collections import deque
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider

from app.core.constants import (
    MAX_CONCURRENT_ICON_WORKERS,
    MAX_ICON_CACHE_SIZE_MB,
    WORKER_TIMEOUT_MS,
)
from app.services.icon_batch_worker import IconBatchWorker
from app.services.windows_icon_converter import hicon_to_qpixmap_at_size


class IconService:
    """Service for providing native Windows file icons."""

    # Límite de workers concurrentes para evitar saturación de CPU/memoria
    MAX_CONCURRENT_WORKERS = MAX_CONCURRENT_ICON_WORKERS
    
    # Límite de cache en bytes
    MAX_CACHE_SIZE_BYTES = MAX_ICON_CACHE_SIZE_MB * 1024 * 1024

    def __init__(self):
        """Initialize IconService with icon provider and cache."""
        self._icon_provider = QFileIconProvider()
        self._icon_cache: dict[str, QIcon] = {}
        self._icon_cache_mtime: dict[str, float] = {}  # Track file mtime for cache validation
        self._icon_cache_access: dict[str, int] = {}  # LRU: track access order
        self._icon_cache_size: dict[str, int] = {}  # Estimated size in bytes per cache entry
        self._cache_access_counter = 0  # Counter for LRU ordering
        self._active_workers: List[IconBatchWorker] = []  # Lista de workers activos
        self._pending_jobs: deque = deque()  # Cola de trabajos pendientes
        # Cache de timestamps de verificación de mtime (optimización)
        self._mtime_cache_timestamp: dict[str, float] = {}  # Última vez que se verificó mtime
        self._mtime_check_interval: float = 5.0  # Verificar mtime máximo cada 5 segundos

    def get_file_icon(self, file_path: str, size: QSize = None) -> QIcon:
        """Get native Windows icon for a file."""
        if not file_path or not os.path.isfile(file_path):
            return self._get_default_icon()

        _, ext = os.path.splitext(file_path)
        ext = ext.lower() if ext else ""

        cache_key = f"{ext}_{size.width() if size else 'default'}"
        
        # Check cache validity: verify file mtime hasn't changed
        if cache_key in self._icon_cache:
            # Optimización: solo verificar mtime si pasó tiempo suficiente desde última verificación
            last_check = self._mtime_cache_timestamp.get(cache_key, 0)
            current_time = time.time()
            
            if current_time - last_check < self._mtime_check_interval:
                # Aún dentro del intervalo, usar cache sin verificar mtime
                self._cache_access_counter += 1
                self._icon_cache_access[cache_key] = self._cache_access_counter
                return self._icon_cache[cache_key]
            
            # Verificar mtime solo si pasó tiempo suficiente
            cached_mtime = self._icon_cache_mtime.get(cache_key, 0)
            try:
                current_mtime = os.path.getmtime(file_path)
                self._mtime_cache_timestamp[cache_key] = current_time  # Actualizar timestamp de verificación
                
                if current_mtime == cached_mtime:
                    # Actualizar acceso LRU
                    self._cache_access_counter += 1
                    self._icon_cache_access[cache_key] = self._cache_access_counter
                    return self._icon_cache[cache_key]
                else:
                    # File changed, invalidate cache entry
                    self._remove_cache_entry(cache_key)
            except (OSError, ValueError):
                # File doesn't exist or can't read mtime, invalidate cache
                self._remove_cache_entry(cache_key)

        qfile_info = QFileInfo(file_path)
        icon = self._icon_provider.icon(qfile_info)
        
        if size:
            pixmap = self._get_best_quality_pixmap(icon, size)
            icon = QIcon(pixmap)

        if ext:
            # Estimar tamaño del icono en bytes (width * height * 4 bytes por píxel RGBA)
            estimated_size = self._estimate_icon_size(icon, size)
            
            # Verificar límite de cache antes de agregar
            self._ensure_cache_space(estimated_size)
            
            # Agregar al cache
            self._icon_cache[cache_key] = icon
            self._icon_cache_size[cache_key] = estimated_size
            self._cache_access_counter += 1
            self._icon_cache_access[cache_key] = self._cache_access_counter
            try:
                self._icon_cache_mtime[cache_key] = os.path.getmtime(file_path)
            except (OSError, ValueError):
                self._icon_cache_mtime[cache_key] = 0

        return icon

    def get_folder_icon(self, folder_path: str = None, size: QSize = None) -> QIcon:
        """Get native Windows icon for a folder."""
        if folder_path and os.path.isdir(folder_path):
            qfile_info = QFileInfo(folder_path)
            icon = self._icon_provider.icon(qfile_info)
        else:
            icon = self._icon_provider.icon(QFileIconProvider.IconType.Folder)

        if size:
            return QIcon(icon.pixmap(size))
        return icon

    def get_file_icon_pixmap(
        self, 
        file_path: str, 
        size: QSize, 
        device_pixel_ratio: float = 1.0
    ) -> QPixmap:
        """Get pixmap directly for maximum sharpness (avoids double scaling)."""
        if not file_path or not os.path.isfile(file_path):
            default_icon = self._get_default_icon()
            high_dpi_size = QSize(
                int(size.width() * device_pixel_ratio), 
                int(size.height() * device_pixel_ratio)
            )
            pixmap = default_icon.pixmap(high_dpi_size)
            pixmap.setDevicePixelRatio(device_pixel_ratio)
            return pixmap
        
        qfile_info = QFileInfo(file_path)
        icon = self._icon_provider.icon(qfile_info)
        
        high_dpi_size = QSize(
            int(size.width() * device_pixel_ratio), 
            int(size.height() * device_pixel_ratio)
        )
        
        pixmap = self._get_best_quality_pixmap(icon, high_dpi_size)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        return pixmap


    def _get_best_quality_pixmap(self, icon: QIcon, target_size: QSize) -> QPixmap:
        """Get pixmap at best available quality, scaling to fill exact size."""
        available_sizes = icon.availableSizes()
        
        if available_sizes:
            best_size = max(available_sizes, key=lambda s: s.width() * s.height())
            pixmap = icon.pixmap(best_size)
            
            if pixmap.width() != target_size.width() or pixmap.height() != target_size.height():
                # Use SmoothTransformation for high quality (like PDFs)
                pixmap = pixmap.scaled(
                    target_size.width(), target_size.height(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            return pixmap
        else:
            high_dpi_size = QSize(target_size.width() * 2, target_size.height() * 2)
            pixmap_2x = icon.pixmap(high_dpi_size)
            return pixmap_2x.scaled(
                target_size.width(), target_size.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

    def _get_default_icon(self) -> QIcon:
        """Get default document icon when file icon unavailable."""
        return self._icon_provider.icon(QFileIconProvider.IconType.File)

    def generate_icons_batch_async(
        self,
        file_paths: List[str],
        size: QSize,
        on_finished: Callable[[List[Tuple[str, QPixmap]]], None],
        on_progress: Optional[Callable[[int], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        priority: bool = False
    ) -> None:
        """
        Generate multiple icons asynchronously using QThread worker.
        
        Implementa cola de trabajos con límite de workers concurrentes (máximo 4)
        para evitar saturación de CPU/memoria. Los trabajos con priority=True se
        procesan antes que los normales.
        
        Args:
            file_paths: List of file paths to generate icons for.
            size: Size for generated icons.
            on_finished: Callback called with list of (path, QPixmap) tuples when complete.
            on_progress: Optional callback called with progress percentage (0-100).
            on_error: Optional callback called with error message on failure.
            priority: If True, job is added to front of queue (for visible icons).
        """
        # Crear trabajo
        job = {
            'file_paths': file_paths,
            'size': size,
            'on_finished': on_finished,
            'on_progress': on_progress,
            'on_error': on_error
        }
        
        # Agregar a cola (al frente si es prioritario)
        if priority:
            self._pending_jobs.appendleft(job)
        else:
            self._pending_jobs.append(job)
        
        # Intentar procesar trabajos pendientes
        self._process_queue()
    
    def _process_queue(self) -> None:
        """Procesar trabajos de la cola hasta alcanzar el límite de workers."""
        # Limpiar workers terminados
        self._active_workers = [w for w in self._active_workers if w.isRunning()]
        
        # Procesar trabajos mientras haya espacio y trabajos pendientes
        while len(self._active_workers) < self.MAX_CONCURRENT_WORKERS and self._pending_jobs:
            job = self._pending_jobs.popleft()
            self._start_worker(job)
    
    def _start_worker(self, job: dict) -> None:
        """Iniciar un worker para procesar un trabajo."""
        worker = IconBatchWorker(
            job['file_paths'],
            job['size'],
            self._icon_provider
        )
        self._active_workers.append(worker)
        
        def handle_finished(results: List[Tuple[str, QPixmap]]) -> None:
            # Remover worker de lista activa
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            # Procesar siguiente trabajo en cola
            self._process_queue()
            # Llamar callback del trabajo
            job['on_finished'](results)
        
        def handle_progress(progress_pct: int) -> None:
            if job['on_progress']:
                job['on_progress'](progress_pct)
        
        def handle_error(error_msg: str) -> None:
            # Remover worker de lista activa
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            # Procesar siguiente trabajo en cola
            self._process_queue()
            # Llamar callback de error o finalización
            if job['on_error']:
                job['on_error'](error_msg)
            else:
                job['on_finished']([])  # Return empty list on error
        
        worker.finished.connect(handle_finished)
        worker.progress.connect(handle_progress)
        worker.error.connect(handle_error)
        worker.start()

    def _estimate_icon_size(self, icon: QIcon, size: Optional[QSize]) -> int:
        """
        Estimar tamaño del icono en bytes.
        
        Usa el tamaño más grande disponible del icono o el tamaño especificado.
        Estimación: width * height * 4 bytes (RGBA).
        """
        if size:
            return size.width() * size.height() * 4
        
        # Usar el tamaño más grande disponible
        available_sizes = icon.availableSizes()
        if available_sizes:
            largest = max(available_sizes, key=lambda s: s.width() * s.height())
            return largest.width() * largest.height() * 4
        
        # Tamaño por defecto si no hay información (64x64)
        return 64 * 64 * 4
    
    def _get_total_cache_size(self) -> int:
        """Obtener tamaño total del cache en bytes."""
        return sum(self._icon_cache_size.values())
    
    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remover entrada del cache y actualizar estructuras."""
        if cache_key in self._icon_cache:
            del self._icon_cache[cache_key]
        if cache_key in self._icon_cache_mtime:
            del self._icon_cache_mtime[cache_key]
        if cache_key in self._icon_cache_access:
            del self._icon_cache_access[cache_key]
        if cache_key in self._icon_cache_size:
            del self._icon_cache_size[cache_key]
        if cache_key in self._mtime_cache_timestamp:
            del self._mtime_cache_timestamp[cache_key]
    
    def _ensure_cache_space(self, new_entry_size: int) -> None:
        """
        Asegurar que hay espacio en cache para nueva entrada.
        
        Usa estrategia LRU: elimina entradas menos usadas recientemente
        hasta que haya espacio suficiente.
        """
        current_size = self._get_total_cache_size()
        target_size = current_size + new_entry_size
        
        # Si excede el límite, limpiar entradas LRU
        if target_size > self.MAX_CACHE_SIZE_BYTES:
            # Ordenar por acceso (menor acceso = más antiguo)
            sorted_keys = sorted(
                self._icon_cache_access.keys(),
                key=lambda k: self._icon_cache_access[k]
            )
            
            # Eliminar entradas más antiguas hasta tener espacio
            for cache_key in sorted_keys:
                if target_size <= self.MAX_CACHE_SIZE_BYTES * 0.8:  # Limpiar hasta 80% del límite
                    break
                entry_size = self._icon_cache_size.get(cache_key, 0)
                self._remove_cache_entry(cache_key)
                target_size -= entry_size
    
    def clear_cache(self) -> None:
        """Clear icon cache to free memory."""
        self._icon_cache.clear()
        self._icon_cache_mtime.clear()
        self._icon_cache_access.clear()
        self._icon_cache_size.clear()
        self._mtime_cache_timestamp.clear()
        self._cache_access_counter = 0
    
    def cancel_all_workers(self) -> None:
        """Cancel all active workers and clear pending jobs queue."""
        # Cancelar todos los workers activos
        for worker in self._active_workers:
            if worker.isRunning():
                worker.cancel()
                worker.terminate()
                worker.wait(WORKER_TIMEOUT_MS)
        
        self._active_workers.clear()
        self._pending_jobs.clear()
    
    def get_active_workers_count(self) -> int:
        """Get number of currently active workers."""
        # Limpiar workers terminados
        self._active_workers = [w for w in self._active_workers if w.isRunning()]
        return len(self._active_workers)
    
    def get_pending_jobs_count(self) -> int:
        """Get number of pending jobs in queue."""
        return len(self._pending_jobs)
