class Todo {
  final String id;
  final String title;
  bool isCompleted;
  final DateTime createdAt;
  final int priority; // 1 = low, 2 = medium, 3 = high

  Todo({
    required this.id,
    required this.title,
    this.isCompleted = false,
    required this.createdAt,
    this.priority = 2,
  });

  /// Toggle completion status
  void toggleCompletion() {
    isCompleted = !isCompleted;
  }

  /// Create a copy with modified fields
  Todo copyWith({
    String? id,
    String? title,
    bool? isCompleted,
    DateTime? createdAt,
    int? priority,
  }) {
    return Todo(
      id: id ?? this.id,
      title: title ?? this.title,
      isCompleted: isCompleted ?? this.isCompleted,
      createdAt: createdAt ?? this.createdAt,
      priority: priority ?? this.priority,
    );
  }

  @override
  String toString() => 'Todo(id: $id, title: $title, completed: $isCompleted)';
}

/// Manages todo list state
class TodoManager {
  final List<Todo> todos = [];
  final List<String> _interactionLog = [];

  /// Add a new todo
  void addTodo(String title, {int priority = 2}) {
    if (title.trim().isEmpty) return;

    final todo = Todo(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title.trim(),
      priority: priority,
      createdAt: DateTime.now(),
    );

    todos.add(todo);
    _log('added', title);
  }

  /// Delete a todo by ID
  void deleteTodo(String id) {
    final todo = todos.firstWhere((t) => t.id == id, orElse: () => Todo(
      id: '',
      title: '',
      createdAt: DateTime.now(),
    ));

    if (todo.title.isNotEmpty) {
      todos.removeWhere((t) => t.id == id);
      _log('deleted', todo.title);
    }
  }

  /// Toggle todo completion
  void toggleTodo(String id) {
    final index = todos.indexWhere((t) => t.id == id);
    if (index != -1) {
      todos[index].toggleCompletion();
      _log('toggled', todos[index].title);
    }
  }

  /// Clear all todos
  void clearAll() {
    todos.clear();
    _log('cleared', 'all');
  }

  /// Mark all todos as complete
  void markAllComplete() {
    for (var todo in todos) {
      todo.isCompleted = true;
    }
    _log('completed', 'all');
  }

  /// Get completed todos
  List<Todo> getCompleted() => todos.where((t) => t.isCompleted).toList();

  /// Get active (incomplete) todos
  List<Todo> getActive() => todos.where((t) => !t.isCompleted).toList();

  /// Search todos by title
  List<Todo> search(String query) {
    if (query.isEmpty) return todos;
    return todos
        .where((t) => t.title.toLowerCase().contains(query.toLowerCase()))
        .toList();
  }

  /// Get stats
  Map<String, int> getStats() {
    return {
      'total': todos.length,
      'completed': getCompleted().length,
      'active': getActive().length,
    };
  }

  /// Internal logging
  void _log(String action, String subject) {
    _interactionLog.add('[$action] $subject');
  }

  /// Get interaction logs
  List<String> getLogs() => List.from(_interactionLog);

  /// Clear logs
  void clearLogs() => _interactionLog.clear();
}
