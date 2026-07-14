import pygame
import math
from pygame.math import Vector2

# Initialize Pygame
pygame.init()
pygame.font.init()

# Screen Configurations
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BONK.PYGM - Interactive Map Maker")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 16)

# Colors Mapping
COLOR_PALETTE = ["black", "grey", "red", "blue", "yellow", "orange", "purple", "pink", "white"]

# Application States
class ToolMode:
    RECT = 0
    LINE = 1
    PLAYER = 2

# Editor State Variables
current_mode = ToolMode.RECT
camera_offset = Vector2(0, 0)
is_panning = False
pan_start = Vector2(0, 0)

# Object Creation Configurations
selected_color_idx = 0
is_death_hazard = False
bouncy_value = 0.0          # 0.0 means False/Normal elasticity
facing_angle = 0
rect_width = 100
rect_height = 40

# Temporary placement states
line_start_point = None

# Placed Data Collections
placed_rects = []
placed_lines = []
placed_players = []

# ID Counters for generation naming
rect_count = 0
line_count = 0
player_count = 0

def get_world_pos(mouse_pos):
    """Converts Pygame Screen Coordinates to engine World Coordinates (Inverting Y axis)"""
    x = mouse_pos[0] - camera_offset.x
    # Inverted Y axis logic to align with Pymunk's positive_y_is_up world coordinates
    y = (HEIGHT - mouse_pos[1]) - camera_offset.y
    return Vector2(x, y)

def get_screen_pos(world_pos):
    """Converts Engine World Coordinates back to Pygame Screen Coordinates"""
    x = world_pos.x + camera_offset.x
    y = HEIGHT - (world_pos.y + camera_offset.y)
    return (int(x), int(y))

def export_map_to_file(filename="generated_map.txt"):
    """Compiles visual elements into raw python string configurations compatible with exec()"""
    lines_to_write = []
    lines_to_write.append("# Generated Map Layout\n")
    
    # 1. Export Players
    lines_to_write.append("# players\n")
    player_keys = [
        ("(pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_LCTRL)", "red"),
        ("(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN)", "blue"),
        ("(pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, None)", "yellow"),
        ("(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, None)", "purple")
    ]
    for i, p in enumerate(placed_players):
        p_id = f"p_{i+1}" if i < 2 else f"debug_{i-1}" if i < 4 else f"custom_{i}"
        p_name = p_id.upper()
        ctrls, def_col = player_keys[i] if i < len(player_keys) else ("(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, None)", p['col'])
        lines_to_write.append(f'players["{p_id}"] = Player("{p_name}", {p["pos"].x}, {p["pos"].y}, "{p["col"]}", *{ctrls})\n')
        
    lines_to_write.append("\nglobal player_collision_status\nplayer_collision_status = False\n\n# Map Geometry\n")
    
    # 2. Export Rectangles
    for r in placed_rects:
        opts = []
        if r['facing'] != 0: opts.append(f"facing = {r['facing']}")
        if r['bouncy'] > 0: opts.append(f"bouncy = {r['bouncy']}")
        if r['death']: opts.append("death = True")
        
        opt_str = ", ".join(opts)
        opt_str = f", {opt_str}" if opt_str else ""
        
        lines_to_write.append(
            f'rects["{r["id"]}"] = Rect("{r["col"]}", pygame.math.Vector2({r["center"].x}, {r["center"].y}), {r["w"]}, {r["h"]}{opt_str})\n'
        )
        
    # 3. Export Lines
    for l in placed_lines:
        opts = []
        if l['bouncy'] > 0: opts.append(f"bouncy = {l['bouncy']}")
        if l['death']: opts.append("death = True")
        
        opt_str = ", ".join(opts)
        opt_str = f", {opt_str}" if opt_str else ""
        
        lines_to_write.append(
            f'rects["{l["id"]}"] = Line("{l["col"]}", Vector2({l["pos1"].x}, {l["pos1"].y}), Vector2({l["pos2"].x}, {l["pos2"].y}){opt_str})\n'
        )
        
    lines_to_write.append("\nglobal global_movement\nglobal_movement.y = -10\n")
    
    with open(filename, "w") as f:
        f.writelines(lines_to_write)
    print(f"Map successfully compiled and written to {filename}")

# Main loop
running = True
while running:
    mouse_screen_pos = pygame.mouse.get_pos()
    mouse_world_pos = get_world_pos(mouse_screen_pos)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Keyboard Event Controls
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: current_mode = ToolMode.RECT
            elif event.key == pygame.K_2: current_mode = ToolMode.LINE
            elif event.key == pygame.K_3: current_mode = ToolMode.PLAYER
            
            # Property Adjustments
            elif event.key == pygame.K_c:  # Cycle active colors
                selected_color_idx = (selected_color_idx + 1) % len(COLOR_PALETTE)
            elif event.key == pygame.K_x:  # Toggle Hazard Zone status
                is_death_hazard = not is_death_hazard
            elif event.key == pygame.K_b:  # Adjust Bouncy value intervals
                bouncy_value = 0.0 if bouncy_value >= 4.0 else bouncy_value + 0.5
            elif event.key == pygame.K_r:  # Increment design angle
                facing_angle = (facing_angle + 15) % 360
            elif event.key == pygame.K_f:  # Decrement design angle
                facing_angle = (facing_angle - 15) % 360
                
            # Rectangle Sizing Modifiers
            elif event.key == pygame.K_UP: rect_height += 10
            elif event.key == pygame.K_DOWN: rect_height = max(5, rect_height - 10)
            elif event.key == pygame.K_RIGHT: rect_width += 10
            elif event.key == pygame.K_LEFT: rect_width = max(5, rect_width - 10)
            
            # File Export Key
            elif event.key == pygame.K_s:
                export_map_to_file()
                
        # Mouse Input Processing
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2 or (event.button == 1 and pygame.key.get_mods() & pygame.KMOD_SHIFT): 
                # Middle Click or Shift+Left Click starts camera panning
                is_panning = True
                pan_start = Vector2(mouse_screen_pos)
            elif event.button == 1: # Left click interactions
                color = COLOR_PALETTE[selected_color_idx]
                
                if current_mode == ToolMode.RECT:
                    rect_count += 1
                    placed_rects.append({
                        "id": f"rect_gen_{rect_count}", "col": color, "center": mouse_world_pos,
                        "w": rect_width, "h": rect_height, "facing": facing_angle,
                        "bouncy": bouncy_value, "death": is_death_hazard
                    })
                elif current_mode == ToolMode.LINE:
                    if line_start_point is None:
                        line_start_point = mouse_world_pos
                    else:
                        line_count += 1
                        placed_lines.append({
                            "id": f"line_gen_{line_count}", "col": color, "pos1": line_start_point,
                            "pos2": mouse_world_pos, "bouncy": bouncy_value, "death": is_death_hazard
                        })
                        line_start_point = None # Reset
                elif current_mode == ToolMode.PLAYER:
                    placed_players.append({
                        "pos": mouse_world_pos, "col": color
                    })
                    
            elif event.button == 3: # Right click resets active placement selections
                line_start_point = None

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2 or event.button == 1:
                is_panning = False
                
        elif event.type == pygame.MOUSEMOTION:
            if is_panning:
                delta = Vector2(mouse_screen_pos) - pan_start
                # Adjust camera offset matching axis inversion rule
                camera_offset.x += delta.x
                camera_offset.y -= delta.y 
                pan_start = Vector2(mouse_screen_pos)

    # --- RENDERING PIPELINE ---
    screen.fill((40, 40, 45)) # Dark background canvas
    
    # Render Placed Rectangles
    for r in placed_rects:
        scr_center = get_screen_pos(r['center'])
        # Generating a rotated surface visualization tracking facing angles
        surf = pygame.Surface((r['w'], r['h']), pygame.SRCALPHA)
        surf.fill(pygame.Color(r['col']))
        if r['death']: pygame.draw.rect(surf, (255, 0, 0), (0,0, r['w'], r['h']), 2) # Hazard border
        if r['bouncy'] > 0: pygame.draw.rect(surf, (255, 255, 0), (0,0, r['w'], r['h']), 1)
        
        # Pygame uses clockwise angles; negate facing parameter to match original math functions
        rotated_surf = pygame.transform.rotate(surf, r['facing'])
        new_rect = rotated_surf.get_rect(center=scr_center)
        screen.blit(rotated_surf, new_rect.topleft)

    # Render Placed Lines
    for l in placed_lines:
        p1 = get_screen_pos(l['pos1'])
        p2 = get_screen_pos(l['pos2'])
        col = pygame.Color(l['col'])
        pygame.draw.line(screen, col, p1, p2, 6)
        if l['death']: pygame.draw.line(screen, (255, 0, 0), p1, p2, 2)

    # Render Placed Players
    for p in placed_players:
        pos = get_screen_pos(p['pos'])
        pygame.draw.circle(screen, pygame.Color(p['col']), pos, 20)
        pygame.draw.circle(screen, (255, 255, 255), pos, 20, 2)

    # Render Placement Previews
    color = COLOR_PALETTE[selected_color_idx]
    if current_mode == ToolMode.RECT:
        scr_center = get_screen_pos(mouse_world_pos)
        surf = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
        surf.fill((*pygame.Color(color)[:3], 130)) # Translucent preview
        rotated_surf = pygame.transform.rotate(surf, facing_angle)
        screen.blit(rotated_surf, rotated_surf.get_rect(center=scr_center).topleft)
        
    elif current_mode == ToolMode.LINE:
        if line_start_point:
            p1 = get_screen_pos(line_start_point)
            pygame.draw.line(screen, pygame.Color(color), p1, mouse_screen_pos, 4)
            
    elif current_mode == ToolMode.PLAYER:
        pygame.draw.circle(screen, (*pygame.Color(color)[:3], 130), mouse_screen_pos, 20)

    # --- HEADS UP DISPLAY / INTERFACE OVERLAY ---
    # Top overlay bar
    pygame.draw.rect(screen, (20, 20, 25), (0, 0, WIDTH, 40))
    mode_str = ["RECTANGLE", "LINE", "PLAYER"][current_mode]
    hud_text = f"Mode: [1,2,3]: {mode_str} | Color [C]: {color} | Death [X]: {is_death_hazard} | Bouncy [B]: {bouncy_value} | Facing [R/F]: {facing_angle}°"
    screen.blit(font.render(hud_text, True, (240, 240, 240)), (15, 12))
    
    # Bottom control bar
    pygame.draw.rect(screen, (20, 20, 25), (0, HEIGHT-35, WIDTH, 35))
    controls_text = "Arrows: Size Rect | Shift+Mouse1 / Middle Mouse: Pan Camera | Mouse2: Cancel | Press [S] to Export generated_map.txt"
    screen.blit(font.render(controls_text, True, (180, 180, 180)), (15, HEIGHT - 25))
    
    # Crosshair tracking global 0,0 position
    origin_screen = get_screen_pos(Vector2(0, 0))
    if 0 <= origin_screen[0] <= WIDTH and 0 <= origin_screen[1] <= HEIGHT:
        pygame.draw.line(screen, (100, 255, 100), (origin_screen[0]-15, origin_screen[1]), (origin_screen[0]+15, origin_screen[1]), 1)
        pygame.draw.line(screen, (100, 255, 100), (origin_screen[0], origin_screen[1]-15), (origin_screen[0], origin_screen[1]+15), 1)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()