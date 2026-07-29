"""
Módulo para Pattern Lock Android usando Custom Components V2
"""

import streamlit as st
import streamlit.components.v2 as components
import math
import json

def create_pattern_component():
    """
    Cria o componente de pattern lock usando a API V2 do Streamlit
    """
    html_content = """
    <div class="pattern-container">
        <div class="pattern-header">
            <h3>🔒 Padrão Android</h3>
            <p>Clique ou arraste para criar o padrão</p>
        </div>
        
        <div class="pattern-grid-container" id="gridContainer">
            <div class="pattern-grid" id="patternGrid"></div>
            <div id="linesContainer"></div>
        </div>
        
        <div class="pattern-result">
            <strong>Padrão:</strong> <span id="patternResult">Nenhum</span>
        </div>
        
        <div class="pattern-controls">
            <button class="pattern-btn pattern-clear" onclick="handleClear()">🔄 Limpar</button>
        </div>
        
        <div class="pattern-hint">
            Mínimo: 3 pontos • Máximo: 9 pontos • Sem repetições
        </div>
    </div>
    """

    css_content = """
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .pattern-container {
        max-width: 100%;
        margin: 0 auto;
        text-align: center;
        background: var(--secondary-background-color, #262730);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid var(--border-color, #555);
        min-height: 520px;
    }
    
    .pattern-header {
        margin-bottom: 20px;
    }
    
    .pattern-grid-container {
        position: relative;
        width: 270px;
        height: 270px;
        margin: 0 auto 25px;
        touch-action: none;
    }
    
    .pattern-grid {
        display: grid;
        grid-template-columns: repeat(3, 90px);
        grid-template-rows: repeat(3, 90px);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    
    .pattern-dot {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        z-index: 2;
    }
    
    .pattern-dot-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: var(--background-color, #e0e0e0);
        border: 2px solid var(--border-color, #bdbdbd);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        color: var(--text-color, #666);
        cursor: pointer;
        transition: all 0.2s;
        user-select: none;
    }
    
    .pattern-dot.selected .pattern-dot-circle {
        background: var(--primary-color, #2196f3);
        border-color: var(--primary-color-dark, #1976d2);
        color: white;
        transform: scale(1.2);
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.4);
    }
    
    .pattern-line {
        position: absolute;
        background: var(--primary-color, #2196f3);
        height: 4px;
        transform-origin: 0 0;
        z-index: 1;
        pointer-events: none;
        border-radius: 2px;
    }
    
    .pattern-result {
        background: var(--secondary-background-color, #e3f2fd);
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid var(--border-color, #bbdefb);
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        color: var(--text-color, #000000);
    }

    .pattern-result strong {
        color: var(--text-color, #1f2937);
        margin-bottom: 5px;
        font-size: 14px;
    }

    #patternResult {
        color: var(--primary-color, #dc2626);
        font-family: 'Courier New', monospace;
        font-size: 18px;
        font-weight: bold;
        word-break: break-all;
    }
            
    .pattern-controls {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 25px;
        padding: 10px 0;
    }
    
    .pattern-btn {
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s;
        min-width: 120px;
        flex: 1;
        max-width: 140px;
    }
    
    .pattern-clear {
        background: var(--error-color, #e44444);
        color: white;
    }
    
    .pattern-clear:hover {
        background: var(--error-color-dark, #d32f2f);
        transform: translateY(-1px);
    }
    
    .pattern-hint {
        font-size: 12px;
        color: var(--text-muted, #9ca3af);
        margin-top: 15px;
        line-height: 1.4;
    }
    """

    js_content = """
    export default function(component) {
        const { setStateValue, parentElement, data } = component;
        
        // Elementos do DOM
        const gridContainer = parentElement.querySelector('#gridContainer');
        const patternGrid = parentElement.querySelector('#patternGrid');
        const linesContainer = parentElement.querySelector('#linesContainer');
        const patternResult = parentElement.querySelector('#patternResult');
        
        // Estado do componente
        const dots = [];
        const selectedDots = [];
        const lines = [];
        const dotPositions = [];
        let isDrawing = false;
        
        // Inicializar o grid
        function initGrid() {
            // Limpar estado anterior
            patternGrid.innerHTML = '';
            dots.length = 0;
            selectedDots.length = 0;
            lines.forEach(line => line.remove());
            lines.length = 0;
            dotPositions.length = 0;
            
            // Calcular posições dos pontos
            const cellSize = 90;
            for (let row = 0; row < 3; row++) {
                for (let col = 0; col < 3; col++) {
                    const x = col * cellSize + cellSize / 2;
                    const y = row * cellSize + cellSize / 2;
                    const number = row * 3 + col + 1;
                    dotPositions.push({x, y, number});
                }
            }
            
            // Criar pontos
            dotPositions.forEach((pos, index) => {
                const dot = document.createElement('div');
                dot.className = 'pattern-dot';
                dot.style.position = 'absolute';
                dot.style.left = (pos.x - 15) + 'px';
                dot.style.top = (pos.y - 15) + 'px';
                
                const dotCircle = document.createElement('div');
                dotCircle.className = 'pattern-dot-circle';
                dotCircle.textContent = pos.number;
                dotCircle.dataset.index = index;
                
                dot.appendChild(dotCircle);
                patternGrid.appendChild(dot);
                dots.push(dotCircle);
            });
            
            // Configurar event listeners
            setupEventListeners();
            
            // Carregar padrão inicial se existir
            if (data && data.initialPattern) {
                loadPattern(data.initialPattern);
            }
            
            updateDisplay();
        }
        
        // Configurar event listeners
        function setupEventListeners() {
            // Eventos de mouse
            gridContainer.addEventListener('mousedown', handleMouseDown);
            gridContainer.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            
            // Eventos de touch
            gridContainer.addEventListener('touchstart', handleTouchStart, {passive: false});
            gridContainer.addEventListener('touchmove', handleTouchMove, {passive: false});
            gridContainer.addEventListener('touchend', handleTouchEnd);
            
            // Eventos para cada ponto
            dots.forEach((dot, index) => {
                dot.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    startDrawing(index);
                });
                
                dot.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    startDrawing(index);
                });
            });
        }
        
        // Funções de desenho
        function startDrawing(index) {
            isDrawing = true;
            addDot(index);
        }
        
        function addDot(index) {
            if (!selectedDots.includes(index)) {
                selectedDots.push(index);
                dots[index].classList.add('selected');
                
                // Conectar com ponto anterior
                if (selectedDots.length > 1) {
                    const prevIndex = selectedDots[selectedDots.length - 2];
                    drawLine(prevIndex, index);
                }
                
                updateDisplay();
                
                // Enviar padrão atualizado para o Streamlit
                const pattern = selectedDots.map(idx => dotPositions[idx].number).join('-');
                setStateValue("pattern", pattern);
            }
        }
        
        function drawLine(fromIndex, toIndex) {
            const fromPos = dotPositions[fromIndex];
            const toPos = dotPositions[toIndex];
            
            const line = document.createElement('div');
            line.className = 'pattern-line';
            
            const deltaX = toPos.x - fromPos.x;
            const deltaY = toPos.y - fromPos.y;
            const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
                        
            line.style.width = length + 'px';
            line.style.left = fromPos.x + 'px';
            line.style.top = fromPos.y + 'px';
            line.style.transform = 'rotate(' + angle + 'deg)';
            line.style.transformOrigin = '0 0';
            
            linesContainer.appendChild(line);
            lines.push(line);
        }
        
        // Utilitários
        function findDotUnderCursor(e) {
            const rect = gridContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            for (let i = 0; i < dotPositions.length; i++) {
                const pos = dotPositions[i];
                const distance = Math.sqrt(
                    Math.pow(x - pos.x, 2) + 
                    Math.pow(y - pos.y, 2)
                );
                
                if (distance < 25) {
                    return i;
                }
            }
            
            return -1;
        }
        
        function updateDisplay() {
            const pattern = selectedDots.length > 0 
                ? selectedDots.map(idx => dotPositions[idx].number).join('-')
                : "Nenhum";
            
            patternResult.textContent = pattern;
        }
        
        // Handlers de eventos
        function handleMouseDown(e) {
            if (e.button === 0) {
                const dotIndex = findDotUnderCursor(e);
                if (dotIndex !== -1) {
                    startDrawing(dotIndex);
                } else {
                    isDrawing = true;
                }
            }
        }
        
        function handleMouseMove(e) {
            if (isDrawing) {
                const dotIndex = findDotUnderCursor(e);
                if (dotIndex !== -1) {
                    addDot(dotIndex);
                }
            }
        }
        
        function handleMouseUp() {
            isDrawing = false;
        }
        
        function handleTouchStart(e) {
            if (e.touches.length === 1) {
                e.preventDefault();
                const dotIndex = findDotUnderCursor(e.touches[0]);
                if (dotIndex !== -1) {
                    startDrawing(dotIndex);
                } else {
                    isDrawing = true;
                }
            }
        }
        
        function handleTouchMove(e) {
            if (isDrawing && e.touches.length === 1) {
                e.preventDefault();
                const dotIndex = findDotUnderCursor(e.touches[0]);
                if (dotIndex !== -1) {
                    addDot(dotIndex);
                }
            }
        }
        
        function handleTouchEnd(e) {
            if (e.touches.length === 0) {
                isDrawing = false;
            }
        }
        
        // Funções de controle
        window.handleClear = function() {
            selectedDots.length = 0;
            lines.forEach(line => line.remove());
            lines.length = 0;
            dots.forEach(dot => dot.classList.remove('selected'));
            updateDisplay();
            setStateValue("pattern", "");
        }
        
        function loadPattern(patternStr) {
            if (!patternStr) return;
            
            try {
                const numbers = patternStr.split('-').map(n => parseInt(n.trim()));
                numbers.forEach(num => {
                    const index = num - 1;
                    if (index >= 0 && index < dots.length) {
                        addDot(index);
                    }
                });
            } catch (error) {
                console.error('Erro ao carregar padrão:', error);
            }
        }
        
        // Inicializar o grid
        initGrid();
    }
    """
    
    return components.component(
        "android_pattern_lock",
        html=html_content,
        js=js_content,
        css=css_content
    )

# Criar instância do componente (singleton)
_pattern_component = None

def get_pattern_component():
    """Obtém a instância do componente pattern lock"""
    global _pattern_component
    if _pattern_component is None:
        _pattern_component = create_pattern_component()
    return _pattern_component

def android_pattern_lock(initial_pattern="", key="pattern_lock"):
    """
    Componente Pattern Lock usando Custom Components V2
    """
    pattern_component = get_pattern_component()
    
    result = pattern_component(
        data={"initialPattern": initial_pattern},
        default={"pattern": ""},
        key=key,
        on_pattern_change=lambda: None
    )
    
    return result.pattern if result else ""

def validate_pattern(pattern_str: str) -> tuple[bool, str]:
    """Valida se um padrão é válido"""
    if not pattern_str:
        return False, "Padrão vazio"
    
    try:
        numbers = [int(n) for n in pattern_str.split('-')]
    except:
        return False, "Formato inválido"
    
    if len(numbers) < 3:
        return False, "Mínimo de 3 pontos necessários"
    
    if len(numbers) > 9:
        return False, "Máximo de 9 pontos permitidos"
    
    if len(numbers) != len(set(numbers)):
        return False, "Não pode repetir números"
    
    if not all(1 <= n <= 9 for n in numbers):
        return False, "Use apenas números de 1 a 9"
    
    return True, ""

def render_pattern_grid(pattern_str: str) -> str:
    """Renderiza uma visualização estática do padrão com linhas"""
    if not pattern_str:
        return "<div style='text-align: center; color: #999; padding: 20px;'>Nenhum padrão definido</div>"
    
    is_valid, error_msg = validate_pattern(pattern_str)
    
    if not is_valid:
        return f"<div style='text-align: center; color: #f44336; padding: 10px;'>⚠️ {error_msg}</div>"
    
    numbers = [int(n.strip()) for n in pattern_str.split('-')]
    
    # Calcular posições dos pontos em um grid 3x3
    positions = []
    for i in range(1, 10):
        row = (i - 1) // 3
        col = (i - 1) % 3
        x = col * 50 + 25  # centro do ponto (25px em um grid de 50px)
        y = row * 50 + 25
        positions.append((x, y, i))
    
    # Container principal
    grid_html = f"""
    <div style="
        position: relative;
        width: 150px;
        height: 150px;
        margin: 0 auto;
    ">
    """
    
    # Desenhar linhas primeiro (para ficarem atrás dos pontos)
    if len(numbers) > 1:
        for i in range(len(numbers) - 1):
            from_num = numbers[i]
            to_num = numbers[i + 1]
            
            from_idx = from_num - 1
            to_idx = to_num - 1
            
            x1, y1, _ = positions[from_idx]
            x2, y2, _ = positions[to_idx]
            
            # Calcular ângulo e comprimento da linha
            dx = x2 - x1
            dy = y2 - y1
            length = (dx**2 + dy**2)**0.5
            angle = math.degrees(math.atan2(dy, dx))
            
            grid_html += f"""
            <div style="
                position: absolute;
                left: {x1}px;
                top: {y1}px;
                width: {length}px;
                height: 4px;
                background: #2196f3;
                transform: rotate({angle}deg);
                transform-origin: 0 0;
                z-index: 1;
            "></div>
            """
    
    # Desenhar pontos
    for x, y, num in positions:
        if num in numbers:
            position_in_pattern = numbers.index(num) + 1
            hue = 200 + (position_in_pattern * 15)
            color = f"hsl({hue}, 70%, 50%)"
            
            grid_html += f"""
            <div style="
                position: absolute;
                left: {x-15}px;
                top: {y-15}px;
                width: 30px;
                height: 30px;
                background: {color};
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #1976d2;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.4);
                z-index: 2;
            ">{num}</div>
            """
        else:
            grid_html += f"""
            <div style="
                position: absolute;
                left: {x-15}px;
                top: {y-15}px;
                width: 30px;
                height: 30px;
                background: #e0e0e0;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdbdbd;
                z-index: 2;
            ">{num}</div>
            """
    
    grid_html += "</div>"
    
    info_html = f"""
    <div style="
        text-align: center;
        margin-top: 10px;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 6px;
        border: 1px solid #e9ecef;
    ">
        <div style="font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold; color: #333;">
            {pattern_str}
        </div>
        <div style="font-size: 12px; color: #666; margin-top: 5px;">
            {len(numbers)} pontos • Mínimo: 3 • Máximo: 9
        </div>
    </div>
    """
    
    return grid_html + info_html

def pattern_editor_modal(order_id: str, current_pattern: str = "") -> str:
    """
    Modal para edição de padrão Android usando Custom Components V2
    """
    pattern_key = f"pattern_editor_{order_id}"
    
    # Inicializar session state
    if f"pattern_editing_{pattern_key}" not in st.session_state:
        st.session_state[f"pattern_editing_{pattern_key}"] = True
    
    with st.container(border=True):
        st.markdown("### 🔒 Editor de Padrão Android")
        
        # Componente principal
        st.markdown("**Desenhe o padrão abaixo:**")
        
        # Usar o novo componente V2
        result = android_pattern_lock(
            initial_pattern=current_pattern,
            key=pattern_key
        )
        
        st.markdown("---")
        
        # Botão aplicar padrão
        
        apply_clicked = st.button(
            "✅ Aplicar Padrão", 
            key=f"apply_{pattern_key}",
            use_container_width=True,
            type="primary"
        )
        
        if apply_clicked:
            if result:
                is_valid, msg = validate_pattern(result)
                if is_valid:
                    st.session_state[f"pattern_editing_{pattern_key}"] = False
                    return result
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("Desenhe um padrão válido primeiro")
        
        # Visualização do padrão atual
        st.markdown("**Padrão atual:**")
        if current_pattern:
            st.html(render_pattern_grid(current_pattern))
        else:
            st.info("📭 Nenhum padrão definido")
    
    return None

def format_pattern_for_display(pattern_str: str) -> str:
    """Formata padrão para exibição amigável"""
    if not pattern_str:
        return "🚫 Nenhum padrão"
    
    is_valid, error_msg = validate_pattern(pattern_str)
    
    if not is_valid:
        return f"⚠️ {error_msg}"
    
    numbers = [int(n.strip()) for n in pattern_str.split('-')]
    return f"🔒 {pattern_str} ({len(numbers)} pontos)"

# Teste
if __name__ == "__main__":
    st.title("🔒 Teste do Pattern Lock V2")
    result = pattern_editor_modal("test", "1-5-9")
    if result:
        st.success(f"Padrão recebido: {result}")
