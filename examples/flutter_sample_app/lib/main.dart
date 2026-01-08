import 'dart:convert';

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
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
            'success': true,
            'message': 'FlutterReflect handler registered (null request)',
          });
        }

        final requestData = jsonDecode(request);
        final command = requestData['command'] as String?;

        switch (command) {
          case 'tapAt':
            final x = (requestData['x'] as num).toDouble();
            final y = (requestData['y'] as num).toDouble();
            await _performTapAt(x, y);
            return jsonEncode({
              'success': true,
              'command': 'tapAt',
              'x': x,
              'y': y,
            });

          case 'scrollAt':
            final x = (requestData['x'] as num).toDouble();
            final y = (requestData['y'] as num).toDouble();
            final dx = (requestData['dx'] as num).toDouble();
            final dy = (requestData['dy'] as num).toDouble();
            final duration = requestData['duration'] as int? ?? 300;
            await _performScrollAt(x, y, dx, dy, duration);
            return jsonEncode({
              'success': true,
              'command': 'scrollAt',
              'x': x,
              'y': y,
              'dx': dx,
              'dy': dy,
            });

          case 'longPressAt':
            final x = (requestData['x'] as num).toDouble();
            final y = (requestData['y'] as num).toDouble();
            final duration = requestData['duration'] as int? ?? 500;
            await _performLongPressAt(x, y, duration);
            return jsonEncode({
              'success': true,
              'command': 'longPressAt',
              'x': x,
              'y': y,
              'duration': duration,
            });

          default:
            return jsonEncode({
              'success': false,
              'error': 'Unknown command: $command',
            });
        }
      } catch (e, stackTrace) {
        return jsonEncode({
          'success': false,
          'error': e.toString(),
          'stackTrace': stackTrace.toString(),
        });
      }
    },
  );

  runApp(const TodoApp());
}

/// Perform a tap at the given coordinates
Future<void> _performTapAt(double x, double y) async {
  final binding = WidgetsBinding.instance;
  final position = Offset(x, y);

  // Create pointer down event
  final downEvent = PointerDownEvent(
    position: position,
    pointer: 1,
    kind: PointerDeviceKind.touch,
  );

  // Create pointer up event
  final upEvent = PointerUpEvent(
    position: position,
    pointer: 1,
    kind: PointerDeviceKind.touch,
  );

  // Dispatch events
  binding.handlePointerEvent(downEvent);
  await Future.delayed(const Duration(milliseconds: 50));
  binding.handlePointerEvent(upEvent);

  // Wait for frame to process
  await binding.endOfFrame;
}

/// Perform a scroll gesture at the given coordinates
Future<void> _performScrollAt(
    double x, double y, double dx, double dy, int durationMs) async {
  final binding = WidgetsBinding.instance;
  final startPosition = Offset(x, y);
  final endPosition = Offset(x + dx, y + dy);

  // Number of move events to simulate smooth scrolling
  const steps = 10;
  final stepDuration = Duration(milliseconds: durationMs ~/ steps);

  // Pointer down
  binding.handlePointerEvent(PointerDownEvent(
    position: startPosition,
    pointer: 2,
    kind: PointerDeviceKind.touch,
  ));

  // Generate move events
  for (int i = 1; i <= steps; i++) {
    await Future.delayed(stepDuration);
    final progress = i / steps;
    final currentPosition = Offset(
      startPosition.dx + (endPosition.dx - startPosition.dx) * progress,
      startPosition.dy + (endPosition.dy - startPosition.dy) * progress,
    );
    binding.handlePointerEvent(PointerMoveEvent(
      position: currentPosition,
      delta: Offset(dx / steps, dy / steps),
      pointer: 2,
      kind: PointerDeviceKind.touch,
    ));
  }

  // Pointer up
  binding.handlePointerEvent(PointerUpEvent(
    position: endPosition,
    pointer: 2,
    kind: PointerDeviceKind.touch,
  ));

  await binding.endOfFrame;
}

/// Perform a long press at the given coordinates
Future<void> _performLongPressAt(double x, double y, int durationMs) async {
  final binding = WidgetsBinding.instance;
  final position = Offset(x, y);

  // Pointer down
  binding.handlePointerEvent(PointerDownEvent(
    position: position,
    pointer: 3,
    kind: PointerDeviceKind.touch,
  ));

  // Wait for long press duration
  await Future.delayed(Duration(milliseconds: durationMs));

  // Pointer up
  binding.handlePointerEvent(PointerUpEvent(
    position: position,
    pointer: 3,
    kind: PointerDeviceKind.touch,
  ));

  await binding.endOfFrame;
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
