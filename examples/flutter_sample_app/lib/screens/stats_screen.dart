import 'package:flutter/material.dart';
import '../models/todo_model.dart';
import '../utils/constants.dart';
import '../widgets/filter_bar.dart';
import '../widgets/todo_item_widget.dart';
import '../widgets/interaction_log.dart';

class StatsScreen extends StatefulWidget {
  final TodoManager todoManager;
  final VoidCallback? onReturn;

  const StatsScreen({
    Key? key,
    required this.todoManager,
    this.onReturn,
  }) : super(key: key);

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  final TextEditingController _searchController = TextEditingController();
  FilterType _currentFilter = FilterType.all;
  String? _currentFeedback;

  @override
  void dispose() {
    _searchController.dispose();
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

  List<Todo> _getFilteredTodos() {
    List<Todo> filtered;

    // Apply filter
    switch (_currentFilter) {
      case FilterType.all:
        filtered = widget.todoManager.todos;
        break;
      case FilterType.active:
        filtered = widget.todoManager.getActive();
        break;
      case FilterType.completed:
        filtered = widget.todoManager.getCompleted();
        break;
    }

    // Apply search
    final query = _searchController.text;
    if (query.isNotEmpty) {
      filtered = filtered
          .where((t) => t.title.toLowerCase().contains(query.toLowerCase()))
          .toList();
      _showFeedback(InteractionMessages.tasksSearched(query));
    } else if (query.isEmpty && _currentFilter != FilterType.all) {
      _showFeedback(
          InteractionMessages.tasksFiltered(filtered.length));
    }

    return filtered;
  }

  void _toggleTodo(String id) {
    final todo = widget.todoManager.todos.firstWhere((t) => t.id == id);
    widget.todoManager.toggleTodo(id);
    _showFeedback(todo.isCompleted
        ? InteractionMessages.taskUncompleted
        : InteractionMessages.taskCompleted);
    setState(() {});
  }

  void _deleteTodo(String id) {
    final todo = widget.todoManager.todos.firstWhere((t) => t.id == id);
    widget.todoManager.deleteTodo(id);
    _showFeedback(InteractionMessages.taskDeleted(todo.title));
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final stats = widget.todoManager.getStats();
    final filteredTodos = _getFilteredTodos();

    return WillPopScope(
      onWillPop: () async {
        widget.onReturn?.call();
        return true;
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Statistics & Filtering'),
          backgroundColor: Colors.purple,
          leading: IconButton(
            key: Key(WidgetKeys.backButton),
            icon: const Icon(Icons.arrow_back),
            onPressed: () {
              widget.onReturn?.call();
              Navigator.pop(context);
            },
          ),
        ),
        body: Column(
          children: [
            // Interaction feedback
            if (_currentFeedback != null)
              InteractionLogWidget(
                message: _currentFeedback!,
              ),

            // Stats section
            Container(
              padding: const EdgeInsets.all(16),
              color: Colors.purple[50],
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Task Statistics',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildStatCard(
                        label: 'Total',
                        value: stats['total'].toString(),
                        color: Colors.blue,
                      ),
                      _buildStatCard(
                        label: 'Completed',
                        value: stats['completed'].toString(),
                        color: Colors.green,
                      ),
                      _buildStatCard(
                        label: 'Active',
                        value: stats['active'].toString(),
                        color: Colors.orange,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      minHeight: 8,
                      value: stats['total'] == 0
                          ? 0
                          : (stats['completed']! / stats['total']!),
                      backgroundColor: Colors.grey[300],
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Colors.green[400]!,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Search section
            Container(
              padding: const EdgeInsets.all(16),
              child: TextField(
                key: Key(WidgetKeys.searchInput),
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search tasks...',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _searchController.clear();
                            setState(() {});
                          },
                        )
                      : null,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  filled: true,
                  fillColor: Colors.grey[100],
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),

            // Filter bar
            FilterBar(
              initialFilter: _currentFilter,
              onFilterChanged: (filter) {
                setState(() {
                  _currentFilter = filter;
                });
              },
            ),

            // Filtered list
            Expanded(
              child: filteredTodos.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.search_off,
                            size: 64,
                            color: Colors.grey[300],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No tasks found',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey[500],
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _searchController.text.isNotEmpty
                                ? 'Try a different search query'
                                : 'No tasks in this category',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[400],
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView(
                      key: Key(WidgetKeys.filteredListView),
                      children: filteredTodos
                          .map((todo) => TodoItemWidget(
                                todo: todo,
                                onTap: () {
                                  _showFeedback(
                                    'Tapped: ${todo.title}',
                                  );
                                },
                                onDelete: () => _deleteTodo(todo.id),
                                onToggle: () => _toggleTodo(todo.id),
                              ))
                          .toList(),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard({
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
