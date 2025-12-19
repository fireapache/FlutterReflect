import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_driver/driver_extension.dart';

import 'models/todo_model.dart';
import 'screens/home_screen.dart';

void main() {
  // Enable FlutterDriver extension for testing and FlutterReflect interaction
  enableFlutterDriverExtension(
    handler: (String? request) async {
      // Handle custom commands from FlutterReflect
      try {
        if (request == null) {
          return jsonEncode({
            'result': 'success',
            'message': 'FlutterReflect handler registered (null request)',
          });
        }

        final requestData = jsonDecode(request);
        final command = requestData['command'] as String?;

        // Example custom commands can be added here
        // For now, just return success to indicate handler is registered
        return jsonEncode({
          'result': 'success',
          'message': 'FlutterReflect handler registered',
          'command': command,
          'timestamp': DateTime.now().toIso8601String(),
        });
      } catch (e) {
        return jsonEncode({
          'result': 'error',
          'message': e.toString(),
        });
      }
    },
  );

  runApp(const TodoApp());
}

class TodoApp extends StatefulWidget {
  const TodoApp({Key? key}) : super(key: key);

  @override
  State<TodoApp> createState() => _TodoAppState();
}

class _TodoAppState extends State<TodoApp> {
  late TodoManager _todoManager;

  @override
  void initState() {
    super.initState();
    _todoManager = TodoManager();

    // Add some sample todos for demonstration
    _todoManager.addTodo('Learn Flutter', priority: 3);
    _todoManager.addTodo('Test FlutterReflect tools', priority: 3);
    _todoManager.addTodo('Review code', priority: 2);
    _todoManager.addTodo('Write documentation', priority: 2);
    _todoManager.addTodo('Deploy app', priority: 3);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Sample Todo App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      home: HomeScreen(
        todoManager: _todoManager,
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}
