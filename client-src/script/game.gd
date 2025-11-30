extends Control

signal send_packet(packet: Dictionary)

@onready var _list: ItemList = $HBoxContainer/VBoxContainer/ItemList
@onready var _action: Button = $HBoxContainer/VBoxContainer/Action
@onready var _canvas: Control = $HBoxContainer/GameCanvas

var players: Array = []
var my_id: String = ""
var player_nodes: Dictionary = {}
var my_position: Vector2 = Vector2(400, 300)
var velocity_y: float = 0.0
const GRAVITY: float = 800.0
const GROUND_Y: float = 300.0


func _ready() -> void:
	if not _canvas:
		_canvas = Control.new()
		_canvas.custom_minimum_size = Vector2(800, 600)
		_canvas.clip_contents = true
		$HBoxContainer.add_child(_canvas)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_A:
			action_move_left()
		elif event.keycode == KEY_D:
			action_move_right()
		elif event.keycode == KEY_SPACE:
			action_jump()


func _process(delta: float) -> void:
	if my_position.y < GROUND_Y:
		velocity_y += GRAVITY * delta
		my_position.y += velocity_y * delta
		if my_position.y >= GROUND_Y:
			my_position.y = GROUND_Y
			velocity_y = 0.0
		_send_position_update()
	
	for player_id in player_nodes:
		var node_data = player_nodes[player_id]
		if node_data.sprite:
			node_data.sprite.position = node_data.sprite.position.lerp(node_data.target_pos, delta * 10.0)
			if node_data.label:
				node_data.label.position = node_data.sprite.position + Vector2(-50, -60)


func start() -> void:
	if _list:
		_list.clear()
	players.clear()
	if _action:
		_action.disabled = false


func stop() -> void:
	if _list:
		_list.clear()
	players.clear()
	if _action:
		_action.disabled = true
	for player_id in player_nodes:
		remove_player_sprite(player_id)
	player_nodes.clear()


func set_player_list(player_array: Array) -> void:
	players = player_array
	if _list:
		_list.clear()
	for p in players:
		if _list:
			_list.add_item(p["name"])
			var idx = _list.item_count - 1
			_list.set_item_tooltip(idx, "UUID: " + p["id"] + "\nOS User: " + p.get("os_username", "unknown"))
		
		if not player_nodes.has(p["id"]):
			create_player_sprite(p["id"], p["name"], p.get("position", {"x": 400, "y": 300}))
		else:
			update_player_label(p["id"], p["name"])


func create_player_sprite(player_id: String, player_name: String, pos: Dictionary) -> void:
	if not _canvas:
		return
	
	var sprite = ColorRect.new()
	sprite.size = Vector2(50, 50)
	sprite.position = Vector2(pos.get("x", 400) - 25, pos.get("y", 300) - 25)
	
	if player_id == my_id:
		sprite.color = Color(0.2, 0.8, 0.2)
	else:
		sprite.color = Color(0.8, 0.2, 0.2)
	
	_canvas.add_child(sprite)
	
	var label = Label.new()
	label.text = player_name
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.position = sprite.position + Vector2(-50, -60)
	label.size = Vector2(150, 30)
	label.add_theme_font_size_override("font_size", 14)
	_canvas.add_child(label)
	
	var initial_pos = Vector2(pos.get("x", 400), pos.get("y", 300))
	
	player_nodes[player_id] = {
		"sprite": sprite,
		"label": label,
		"target_pos": initial_pos
	}
	
	print("[GAME] Created sprite for player: ", player_name, " at ", initial_pos)


func update_player_position(player_id: String, pos: Dictionary) -> void:
	if player_nodes.has(player_id):
		var new_pos = Vector2(pos.get("x", 400), pos.get("y", 300))
		player_nodes[player_id].target_pos = new_pos


func update_player_label(player_id: String, player_name: String) -> void:
	if player_nodes.has(player_id) and player_nodes[player_id].label:
		player_nodes[player_id].label.text = player_name


func remove_player_sprite(player_id: String) -> void:
	if player_nodes.has(player_id):
		if player_nodes[player_id].sprite:
			player_nodes[player_id].sprite.queue_free()
		if player_nodes[player_id].label:
			player_nodes[player_id].label.queue_free()
		player_nodes.erase(player_id)


func handle_network_message(msg: Dictionary) -> void:
	if has_node("HBoxContainer/RichTextLabel"):
		$HBoxContainer/RichTextLabel.add_text(str(msg["name"]) + "\n")


func _emit_packet(packet: Dictionary) -> void:
	send_packet.emit(packet)


func send_action(action_name: String) -> void:
	if action_name == "move_left":
		my_position.x -= 50.0
	elif action_name == "move_right":
		my_position.x += 50.0
	elif action_name == "jump":
		if my_position.y >= GROUND_Y:
			velocity_y = -400.0
	
	if player_nodes.has(my_id):
		player_nodes[my_id].target_pos = my_position
	
	var packet: Dictionary = {
		"type": "action",
		"action": action_name
	}
	_emit_packet(packet)


func _send_position_update() -> void:
	var packet: Dictionary = {
		"type": "position_update",
		"x": my_position.x,
		"y": my_position.y
	}
	_emit_packet(packet)


func action_move_left() -> void:
	send_action("move_left")


func action_move_right() -> void:
	send_action("move_right")


func action_jump() -> void:
	send_action("jump")


func _on_Action_pressed() -> void:
	send_action("move_left")
