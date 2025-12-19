import 'package:flutter/material.dart';
import '../models/todo_model.dart';
import '../utils/constants.dart';

/// Widget for displaying a single todo item
class TodoItemWidget extends StatelessWidget {
  final Todo todo;
  final VoidCallback onTap;
  final VoidCallback onDelete;
  final VoidCallback onToggle;

  const TodoItemWidget({
    Key? key,
    required this.todo,
    required this.onTap,
    required this.onDelete,
    required this.onToggle,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 2,
      child: ListTile(
        key: Key('todoItem_${todo.id}'),
        contentPadding: const EdgeInsets.all(12),
        leading: Checkbox(
          key: Key('${WidgetKeys.todoDonePrefix}${todo.id}'),
          value: todo.isCompleted,
          onChanged: (_) => onToggle(),
          checkColor: Colors.white,
          activeColor: Colors.green,
        ),
        title: Text(
          todo.title,
          key: Key('todoText_${todo.id}'),
          style: TextStyle(
            fontSize: 16,
            decoration: todo.isCompleted ? TextDecoration.lineThrough : null,
            color: todo.isCompleted ? Colors.grey : Colors.black,
          ),
        ),
        subtitle: Text(
          'Priority: ${_getPriorityLabel(todo.priority)} • Created: ${_formatDate(todo.createdAt)}',
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        trailing: IconButton(
          key: Key('${WidgetKeys.deleteButtonPrefix}${todo.id}'),
          icon: const Icon(Icons.delete_outline),
          color: Colors.red,
          onPressed: onDelete,
          tooltip: 'Delete task',
        ),
        onTap: onTap,
      ),
    );
  }

  String _getPriorityLabel(int priority) {
    switch (priority) {
      case 1:
        return 'Low';
      case 2:
        return 'Medium';
      case 3:
        return 'High';
      default:
        return 'Medium';
    }
  }

  String _formatDate(DateTime date) {
    return '${date.month}/${date.day} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
}
