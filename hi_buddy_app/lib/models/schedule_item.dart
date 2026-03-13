class MenuItem {
  String name;
  String image;
  String videoUrl;

  MenuItem({
    required this.name,
    this.image = '',
    this.videoUrl = '',
  });

  factory MenuItem.fromJson(Map<String, dynamic> json) {
    return MenuItem(
      name: json['name'] ?? '',
      image: json['image'] ?? '',
      videoUrl: json['video_url'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'image': image,
        'video_url': videoUrl,
      };
}

class ScheduleItem {
  String time;
  String type;
  String task;
  List<String> guideScript;
  List<MenuItem> menus;
  String videoUrl;
  String status; // 'active', 'past', 'upcoming'

  ScheduleItem({
    required this.time,
    required this.type,
    required this.task,
    this.guideScript = const [],
    this.menus = const [],
    this.videoUrl = '',
    this.status = 'upcoming',
  });

  factory ScheduleItem.fromJson(Map<String, dynamic> json) {
    final menusList = (json['menus'] as List<dynamic>?)
            ?.map((m) => MenuItem.fromJson(m as Map<String, dynamic>))
            .toList() ??
        [];
    final guideList = (json['guide_script'] as List<dynamic>?)
            ?.map((s) => s.toString())
            .toList() ??
        [];

    return ScheduleItem(
      time: json['time'] ?? '00:00',
      type: (json['type'] ?? 'GENERAL').toString().toUpperCase(),
      task: json['task'] ?? '',
      guideScript: guideList,
      menus: menusList,
      videoUrl: json['video_url'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'time': time,
        'type': type,
        'task': task,
        'guide_script': guideScript,
        'menus': menus.map((m) => m.toJson()).toList(),
        if (videoUrl.isNotEmpty) 'video_url': videoUrl,
      };

  int get timeMinutes {
    final parts = time.split(':');
    if (parts.length != 2) return 0;
    return (int.tryParse(parts[0]) ?? 0) * 60 +
        (int.tryParse(parts[1]) ?? 0);
  }
}

class Schedule {
  final String date;
  final List<ScheduleItem> items;

  Schedule({required this.date, required this.items});

  factory Schedule.fromJson(Map<String, dynamic> json) {
    final items = (json['schedule'] as List<dynamic>?)
            ?.map((s) => ScheduleItem.fromJson(s as Map<String, dynamic>))
            .toList() ??
        [];
    items.sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
    return Schedule(date: json['date'] ?? '', items: items);
  }

  Map<String, dynamic> toJson() => {
        'date': date,
        'schedule': items.map((i) => i.toJson()).toList(),
      };
}
