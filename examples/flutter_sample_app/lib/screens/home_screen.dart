import 'package:flutter/material.dart';
import '../models/todo_model.dart';
import '../utils/constants.dart';
import '../widgets/todo_item_widget.dart';
import '../widgets/interaction_log.dart';
import 'stats_screen.dart';

class HomeScreen extends StatefulWidget {
  final TodoManager todoManager;

  const HomeScreen({
    Key? key,
    required this.todoManager,
  }) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _inputController = TextEditingController();
  final InteractionFeedbackManager _feedbackManager =
      InteractionFeedbackManager();
  String? _currentFeedback;

  @override
  void dispose() {
    _inputController.dispose();
    _feedbackManager.dispose();
    super.dispose();
  }

  void _showFeedback(String message) {
    setState(() {
      _currentFeedback = message;
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _currentFeedback = null;
        });
      }
    });
  }

  void _addTodo() {
    final title = _inputController.text;
    if (title.trim().isEmpty) {
      _showFeedback('Please enter a task');
      return;
    }

    widget.todoManager.addTodo(title);
    _inputController.clear();

    _showFeedback(InteractionMessages.taskAdded(title));
    setState(() {});
  }

  void _deleteTodo(String id) {
    final todo = widget.todoManager.todos.firstWhere((t) => t.id == id);
    widget.todoManager.deleteTodo(id);

    _showFeedback(InteractionMessages.taskDeleted(todo.title));
    setState(() {});
  }

  void _toggleTodo(String id) {
    widget.todoManager.toggleTodo(id);
    _showFeedback(widget.todoManager.todos
            .firstWhere((t) => t.id == id)
            .isCompleted
        ? InteractionMessages.taskCompleted
        : InteractionMessages.taskUncompleted);
    setState(() {});
  }

  void _clearAll() {
    if (widget.todoManager.todos.isEmpty) {
      _showFeedback('No tasks to clear');
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear All?'),
        content: const Text('This will delete all tasks. Continue?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              widget.todoManager.clearAll();
              _showFeedback(InteractionMessages.tasksCleared);
              setState(() {});
            },
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  void _markAllComplete() {
    if (widget.todoManager.todos.isEmpty) {
      _showFeedback('No tasks to complete');
      return;
    }

    widget.todoManager.markAllComplete();
    _showFeedback(InteractionMessages.allCompleted);
    setState(() {});
  }

  void _navigateToStats() {
    _showFeedback(InteractionMessages.navigated);
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => StatsScreen(
          todoManager: widget.todoManager,
          onReturn: () {
            _showFeedback(InteractionMessages.returnedHome);
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final stats = widget.todoManager.getStats();
    final todos = widget.todoManager.todos;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Flutter Sample Todo App'),
        backgroundColor: Colors.blue,
        elevation: 4,
        actions: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Center(
              child: Text(
                key: Key(WidgetKeys.statsWidget),
                '${stats['completed']}/${stats['total']} completed',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Interaction feedback display
          if (_currentFeedback != null)
            InteractionLogWidget(
              message: _currentFeedback!,
            ),

          // Input section
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.blue[50],
            child: Column(
              children: [
                TextField(
                  key: Key(WidgetKeys.addTodoInput),
                  controller: _inputController,
                  decoration: InputDecoration(
                    hintText: 'Add a new task...',
                    prefixIcon: const Icon(Icons.add_circle),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  onSubmitted: (_) => _addTodo(),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        key: Key(WidgetKeys.addTodoButton),
                        onPressed: _addTodo,
                        icon: const Icon(Icons.add),
                        label: const Text('Add Task'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      key: Key(WidgetKeys.statsButton),
                      onPressed: _navigateToStats,
                      icon: const Icon(Icons.analytics),
                      label: const Text('Stats'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.purple,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Action buttons
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    key: Key(WidgetKeys.markAllCompleteButton),
                    onPressed: _markAllComplete,
                    icon: const Icon(Icons.check_circle),
                    label: const Text('Mark All Complete'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.green,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    key: Key(WidgetKeys.clearAllButton),
                    onPressed: _clearAll,
                    icon: const Icon(Icons.delete_sweep),
                    label: const Text('Clear All'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Todo list
          Expanded(
            child: todos.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.inbox,
                          size: 64,
                          color: Colors.grey[300],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'No tasks yet',
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.grey[500],
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Add a task above to get started!',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView(
                    key: Key(WidgetKeys.todoListView),
                    children: todos
                        .map((todo) => TodoItemWidget(
                              todo: todo,
                              onTap: () {
                                _showFeedback('Tapped: ${todo.title}');
                              },
                              onDelete: () => _deleteTodo(todo.id),
                              onToggle: () => _toggleTodo(todo.id),
                            ))
                        .toList(),
                  ),
          ),
        ],
      ),
    );
  }
}
