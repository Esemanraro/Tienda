// Funciones para el panel de administración
// -------------------------
// Utils: Loading Overlay
// -------------------------
function showLoading(){
    if(!document.getElementById('globalLoading')){
        const overlay=document.createElement('div');
        overlay.id='globalLoading';
        overlay.className='loading-overlay';
        overlay.innerHTML='<div class="spinner"></div>';
        document.body.appendChild(overlay);
    }
}
function hideLoading(){
    const overlay=document.getElementById('globalLoading');
    if(overlay){ overlay.remove(); }
}

// Obtener token CSRF desde la meta etiqueta o un input oculto
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
}

function initAdminPanel() {
    // Toggle para la sección de gestión de juguetes
    const toyToggleBtn = document.getElementById('toyToggleBtn');
    const toyManagement = document.getElementById('toyManagement');
    const toyToggleIcon = document.getElementById('toyToggleIcon');

    if (toyToggleBtn && toyManagement) {
        toyToggleBtn.addEventListener('click', function() {
            if (toyManagement.style.display === 'none' || toyManagement.style.display === '') {
                toyManagement.style.display = 'block';
            } else {
                toyManagement.style.display = 'none';
            }
            // Actualizar icono
            toyToggleIcon.textContent = toyManagement.style.display === 'block' ? '🔼' : '🔽';
        });
    }

    // Toggle para el formulario de agregar juguete
    const addToyBtn = document.getElementById('addToyBtn');
    const addToyForm = document.getElementById('addToyForm');
    const addToyIcon = document.getElementById('addToyIcon');

    if (addToyBtn && addToyForm) {
        addToyBtn.addEventListener('click', function() {
            if (addToyForm.style.display === 'none' || addToyForm.style.display === '') {
                addToyForm.style.display = 'block';
            } else {
                addToyForm.style.display = 'none';
            }
            addToyIcon.textContent = addToyForm.style.display === 'block' ? '➖' : '➕';
        });
    }

    // Funcionalidad para editar juguetes
    const editButtons = document.querySelectorAll('.edit-toy-btn');
    const editModal = document.getElementById('editToyModal');
    const editForm = document.getElementById('editToyForm');
    const closeEditModal = document.getElementById('closeEditModal');
    const cancelEdit = document.getElementById('cancelEdit');

    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const toyId = this.getAttribute('data-toy-id');
            openEditModal(toyId);
        });
    });

    if (closeEditModal) {
        closeEditModal.addEventListener('click', closeEditModalFunc);
    }

    if (cancelEdit) {
        cancelEdit.addEventListener('click', closeEditModalFunc);
    }

    // Cerrar modal al hacer clic fuera
    if (editModal) {
        editModal.addEventListener('click', function(e) {
            if (e.target === editModal) {
                closeEditModalFunc();
            }
        });
    }

    // Funcionalidad para eliminar juguetes
    const deleteButtons = document.querySelectorAll('.delete-toy-btn');
    const deleteModal = document.getElementById('deleteConfirmModal');
    const deleteForm = document.getElementById('deleteForm');
    const closeDeleteModal = document.getElementById('closeDeleteModal');
    const cancelDelete = document.getElementById('cancelDelete');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const toyId = this.getAttribute('data-toy-id');
            const toyName = this.getAttribute('data-toy-name');

            // SweetAlert2 confirmación
            Swal.fire({
                title: `¿Eliminar "${toyName}"?`,
                text: 'Esta acción no se puede deshacer.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    const csrfToken = getCsrfToken();
                    const deleteData = new URLSearchParams();
                    deleteData.append('csrf_token', csrfToken);

            // Enviar solicitud de eliminación
    fetch(`/admin/toys/${toyId}/delete`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        body: deleteData.toString()
                    }).then(response => {
                        if (response.ok) {
                            hideLoading();
                            Swal.fire('Eliminado', 'El juguete ha sido eliminado.', 'success')
                                .then(() => location.reload());
                        } else {
                            Swal.fire('Error', 'No se pudo eliminar el juguete.', 'error');
                        }
                    }).catch(error => {
                        console.error('Error:', error);
                        Swal.fire('Error', 'No se pudo eliminar el juguete.', 'error');
                    });
                }
            });
        });
    });

    if (closeDeleteModal) {
        closeDeleteModal.addEventListener('click', closeDeleteModalFunc);
    }

    if (cancelDelete) {
        cancelDelete.addEventListener('click', closeDeleteModalFunc);
    }

    // Cerrar modal de eliminación al hacer clic fuera
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                closeDeleteModalFunc();
            }
        });
    }

    // Manejar envío del formulario de edición
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const toyId = document.getElementById('editToyId').value;
            const formData = new FormData(editForm);
            
            // Enviar datos via fetch
            showLoading();
            fetch(`/admin/toys/${toyId}/edit`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    hideLoading();
                    location.reload(); // Recargar la página para mostrar los cambios
                } else {
                    hideLoading();
                    Swal.fire('Error', 'No se pudo actualizar el juguete.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                hideLoading();
                Swal.fire('Error', 'No se pudo actualizar el juguete.', 'error');
            });
        });
    }

    // Manejar envío del formulario de eliminación
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const toyId = document.getElementById('deleteToyId').value;
            const csrfToken = getCsrfToken();
            const deleteData = new URLSearchParams();
            deleteData.append('csrf_token', csrfToken);

            fetch(`/admin/toys/${toyId}/delete`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: deleteData.toString()
            }).then(response => {
                if (response.ok) {
                    location.reload(); // Recargar la página para mostrar los cambios
                } else {
                    hideLoading();
                alert('Error al eliminar el juguete');
                }
            }).catch(error => {
                console.error('Error:', error);
                hideLoading();
                alert('Error al eliminar el juguete');
            });
        });
    }

    // Función para abrir el modal de edición
    function openEditModal(toyId) {
        const editModal = document.getElementById('editToyModal');
        if (!editModal) {
            console.error('Error: No se encontró el modal de edición');
            return;
        }
        
        showLoading();
        fetch(`/admin/toys/${toyId}/edit`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
            .then(response => response.json())
            .then(data => {
                // Llenar el formulario con los datos del juguete
                document.getElementById('editToyId').value = data.id;
                document.getElementById('editName').value = data.name;
                document.getElementById('editDescription').value = data.description || '';
                document.getElementById('editPrice').value = data.price;
                document.getElementById('editCategory').value = data.category;
                document.getElementById('editStock').value = data.stock;
                
                // Mostrar imagen actual si existe
                const imagePreview = document.getElementById('currentImagePreview');
                if (data.image_url) {
                    imagePreview.innerHTML = `
                        <p>Imagen actual:</p>
                        <img src="${data.image_url}" alt="Imagen actual" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 8px;">
                    `;
                } else {
                    imagePreview.innerHTML = '<p>Sin imagen actual</p>';
                }
                
                // Mostrar el modal y ocultar loading
                editModal.style.display = 'flex';
                hideLoading();
            })
            .catch(error => {
                console.error('Error:', error);
                hideLoading();
            alert('Error al cargar los datos del juguete');
            });
    }

    // Función para cerrar el modal de edición
    function closeEditModalFunc() {
        editModal.style.display = 'none';
        editForm.reset();
        document.getElementById('currentImagePreview').innerHTML = '';
    }

    // Función para abrir el modal de eliminación
    function openDeleteModal(toyId, toyName) {
        document.getElementById('deleteToyId').value = toyId;
        document.getElementById('deleteToyName').textContent = toyName;
        deleteModal.style.display = 'flex';
    }

    // Función para cerrar el modal de eliminación
    function closeDeleteModalFunc() {
        deleteModal.style.display = 'none';
    }

    // Cerrar modales con la tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeEditModalFunc();
            closeDeleteModalFunc();
        }
    });

    // --- Filtro y búsqueda en actividad de usuarios ---
    const userSearch = document.getElementById('userSearch');
    const statusFilter = document.getElementById('statusFilter');
    const userCards = document.querySelectorAll('#usersList .user-card');

    function applyUserFilters(){
        const term = userSearch.value.toLowerCase();
        const status = statusFilter.value;
        userCards.forEach(card=>{
            const name=card.dataset.name;
            const isActive=card.dataset.active==='true';
            const isAdmin=card.dataset.admin==='true';
            let visible=true;
            if(term && !name.includes(term)) visible=false;
            if(status==='active' && !isActive) visible=false;
            if(status==='inactive' && isActive) visible=false;
            if(status==='admin' && !isAdmin) visible=false;
            card.style.display = visible? 'block':'none';
        });
    }
    if(userSearch && statusFilter){
        userSearch.addEventListener('input',applyUserFilters);
        statusFilter.addEventListener('change',applyUserFilters);
    }
}

// Función para editar juguete
function editToy(toyId) {
    showLoading();
    
    fetch(`/admin/edit_toy/${toyId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        // Llenar el formulario de edición
        document.getElementById('editToyId').value = data.id;
        document.getElementById('editToyName').value = data.name;
        document.getElementById('editToyDescription').value = data.description;
        document.getElementById('editToyPrice').value = data.price;
        document.getElementById('editToyCategory').value = data.category;
        document.getElementById('editToyStock').value = data.stock;
        
        // Mostrar imagen actual si existe
        if (data.image_url) {
            document.getElementById('currentImage').src = data.image_url;
            document.getElementById('currentImagePreview').style.display = 'block';
        }
        
        // Mostrar el modal
        document.getElementById('editToyModal').style.display = 'block';
    })
    .catch(error => {
        hideLoading();
        showToast('Error al cargar datos del juguete', 'error');
        console.error('Error:', error);
    });
}

// Función para eliminar juguete
function deleteToy(toyId, toyName) {
    if (confirm(`¿Estás seguro de que deseas eliminar "${toyName}"?`)) {
        showLoading();
        
        fetch(`/admin/delete_toy/${toyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showToast('Juguete eliminado exitosamente', 'success');
                // Recargar la página o actualizar la lista
                location.reload();
            } else {
                showToast(data.message || 'Error al eliminar juguete', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showToast('Error al eliminar juguete', 'error');
            console.error('Error:', error);
        });
    }
}

// Función para guardar cambios de edición
function saveToyEdit() {
    const form = document.getElementById('editToyForm');
    const formData = new FormData(form);
    const toyId = document.getElementById('editToyId').value;
    
    // Agregar CSRF token al FormData
    formData.append('csrf_token', getCsrfToken());
    
    showLoading();
    
    fetch(`/admin/edit_toy/${toyId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showToast('Juguete actualizado exitosamente', 'success');
            document.getElementById('editToyModal').style.display = 'none';
            location.reload();
        } else {
            showToast(data.message || 'Error al actualizar juguete', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error al actualizar juguete', 'error');
        console.error('Error:', error);
    });
}

// Función para cerrar modal
function closeEditModal() {
    document.getElementById('editToyModal').style.display = 'none';
}

// Función para mostrar notificaciones
function showToast(message, type = 'info') {
    // Crear elemento toast si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        font-size: 14px;
    `;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Inicializar eventos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Event listeners para botones de edición
    document.querySelectorAll('.edit-toy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const toyId = this.getAttribute('data-toy-id');
            editToy(toyId);
        });
    });
    
    // Event listeners para botones de eliminación
    document.querySelectorAll('.delete-toy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const toyId = this.getAttribute('data-toy-id');
            const toyName = this.getAttribute('data-toy-name');
            deleteToy(toyId, toyName);
        });
    });
    
    // Event listeners para el modal de edición
    const editModal = document.getElementById('editToyModal');
    if (editModal) {
        document.getElementById('closeEditModal').addEventListener('click', closeEditModal);
        document.getElementById('saveToyEdit').addEventListener('click', saveToyEdit);
    }
    
    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        const editModal = document.getElementById('editToyModal');
        if (event.target === editModal) {
            closeEditModal();
        }
    });
});

// Función auxiliar para obtener token CSRF
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content') || 
           document.querySelector('input[name="csrf_token"]').value;
}

// Función auxiliar para mostrar loading
function showLoading() {
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.innerHTML = '<div class="loading-spinner">⏳ Cargando...</div>';
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) loading.remove();
}

// ===== FUNCIÓN SIMPLE PARA BORRAR JUGUETES =====
function deleteToySimple(button) {
    console.log('🗑️ Iniciando eliminación simple de juguete');
    
    const toyId = button.getAttribute('data-toy-id');
    const toyName = button.getAttribute('data-toy-name');
    
    console.log(`🎯 Eliminando juguete ID: ${toyId}, Nombre: ${toyName}`);
    
    if (!toyId) {
        console.error('❌ No se encontró el ID del juguete');
        alert('Error: No se pudo identificar el juguete');
        return;
    }
    
    // Confirmar eliminación
    const confirmMessage = `Estas seguro de que quieres eliminar el juguete "${toyName}"?\n\nEsta accion no se puede deshacer.`;
    if (!confirm(confirmMessage)) {
        console.log('🚫 Eliminación cancelada por el usuario');
        return;
    }
    
    console.log('📡 Enviando request de eliminación...');
    
    // Obtener CSRF token
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    if (!csrfToken) {
        console.error('❌ No se encontró el token CSRF');
        alert('Error: Token de seguridad no encontrado');
        return;
    }
    
    // Crear FormData
    const formData = new FormData();
    formData.append('csrf_token', csrfToken);
    
    // Enviar request
    fetch(`/admin/delete_toy/${toyId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => {
        console.log(`📊 Respuesta de eliminación: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('📋 Datos de respuesta:', data);
        
        if (data.success) {
            console.log('✅ Juguete eliminado exitosamente');
            alert('Juguete eliminado exitosamente');
            
            // Recargar la página para actualizar la lista
            window.location.reload();
        } else {
            console.error('❌ Error en eliminación:', data.message);
            alert(`Error: ${data.message || 'No se pudo eliminar el juguete'}`);
        }
    })
    .catch(error => {
        console.error('❌ Error en fetch:', error);
        alert('Error de conexión. Por favor, intenta nuevamente.');
    });
}
