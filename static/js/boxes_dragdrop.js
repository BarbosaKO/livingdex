document.addEventListener('DOMContentLoaded', () => {
    const slots = document.querySelectorAll('.box-slot');
    let draggedItem = null;
    let sourceSlot = null;

    slots.forEach(slot => {
        // Quando o usuário começa a arrastar um Pokémon
        slot.addEventListener('dragstart', function(e) {
            const pokemonId = this.getAttribute('data-pokemon-id');
            if (!pokemonId) {
                e.preventDefault(); // Não arrasta se o slot estiver vazio
                return;
            }
            draggedItem = this;
            sourceSlot = this.getAttribute('data-slot-num');
            e.dataTransfer.effectAllowed = 'move';
            this.classList.add('dragging');
        });

        // Efeitos visuais ao passar por cima de outro slot
        slot.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        slot.addEventListener('dragleave', function(e) {
            this.classList.remove('drag-over');
        });

        // Quando o usuário solta o Pokémon em um novo slot
        slot.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');

            if (this === draggedItem) return;

            const targetBoxId = this.getAttribute('data-box-id');
            const targetSlotNum = this.getAttribute('data-slot-num');
            const pokemonId = draggedItem.getAttribute('data-pokemon-id');

            // Troca visual imediata (Swap) para não ter delay na UI
            swapVisuals(draggedItem, this);

            // Requisição para o Backend (Flask) salvar a mudança no SQLite
            fetch('/boxes/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pokemon_id: pokemonId,
                    to_box_id: targetBoxId,
                    to_slot: targetSlotNum
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status !== 'success') {
                    alert('Erro ao mover Pokémon: ' + data.message);
                    location.reload(); // Recarrega para restaurar o estado real
                }
            })
            .catch(error => {
                console.error('Erro de rede:', error);
                location.reload();
            });
        });

        slot.addEventListener('dragend', function() {
            this.classList.remove('dragging');
            slots.forEach(s => s.classList.remove('drag-over'));
            draggedItem = null;
        });
    });

    // Função auxiliar para trocar o HTML interno e os atributos data-* entre dois slots
    function swapVisuals(source, target) {
        const sourceHtml = source.innerHTML;
        const sourcePkmId = source.getAttribute('data-pokemon-id');
        
        const targetHtml = target.innerHTML;
        const targetPkmId = target.getAttribute('data-pokemon-id');

        source.innerHTML = targetHtml;
        target.innerHTML = sourceHtml;

        if (targetPkmId) {
            source.setAttribute('data-pokemon-id', targetPkmId);
        } else {
            source.removeAttribute('data-pokemon-id');
        }

        target.setAttribute('data-pokemon-id', sourcePkmId);
    }
});