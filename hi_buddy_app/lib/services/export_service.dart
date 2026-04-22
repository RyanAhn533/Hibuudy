import 'dart:io';
import 'package:excel/excel.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'database_service.dart';
import 'session_service.dart';

/// ══════════════════════════════════════════════════════════
/// ExportService — B2B 복지관/보호자용 수행 기록 엑셀 내보내기
///
/// 박민호 페르소나 요구사항:
/// "월말에 복지부 제출용. 이용자별 수행 기록 표 필수."
///
/// 출력 파일:
/// - 시트 1: 수행 기록 (날짜·활동·완료 여부·단계 진척)
/// - 시트 2: 프로필 (이름·장애 수준·약·연락처)
/// - 시트 3: 이번 주 요약
/// ══════════════════════════════════════════════════════════
class ExportService {
  /// 수행 기록 엑셀 생성 후 공유 (OS 공유 시트 열림)
  /// 반환: 저장된 파일 경로
  static Future<String> exportCompletionLogsToExcel() async {
    final excel = Excel.createExcel();
    // 기본 시트 제거
    excel.delete('Sheet1');

    await _addCompletionSheet(excel);
    await _addProfileSheet(excel);
    await _addWeeklySummarySheet(excel);

    // 파일 저장
    final dir = await getTemporaryDirectory();
    final userName = await SessionService.getUserName();
    final date = DateFormat('yyyyMMdd').format(DateTime.now());
    final fileName = '하루메이트_${userName}_$date.xlsx';
    final path = '${dir.path}/$fileName';
    final bytes = excel.save();
    if (bytes == null) throw Exception('Excel 생성 실패');
    final file = File(path);
    await file.writeAsBytes(bytes, flush: true);

    return path;
  }

  /// 생성 + 즉시 공유 다이얼로그 호출 (카톡·메일·복지관 서버 등)
  static Future<void> exportAndShare() async {
    final path = await exportCompletionLogsToExcel();
    final userName = await SessionService.getUserName();
    final today = DateFormat('yyyy년 M월 d일').format(DateTime.now());
    await Share.shareXFiles(
      [XFile(path)],
      text: '하루메이트 수행 기록\n$userName · $today 기준',
      subject: '하루메이트 수행 기록 · $userName',
    );
  }

  // ── 시트 1: 수행 기록 ──
  static Future<void> _addCompletionSheet(Excel excel) async {
    final sheet = excel['수행 기록'];

    // 헤더
    final headers = ['날짜', '시간', '활동 유형', '할 일', '완료 여부', '단계 완료', '도움 필요'];
    for (int i = 0; i < headers.length; i++) {
      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0));
      cell.value = TextCellValue(headers[i]);
      cell.cellStyle = CellStyle(
        bold: true,
        backgroundColorHex: ExcelColor.fromHexString('#4F7CFF'),
        fontColorHex: ExcelColor.fromHexString('#FFFFFF'),
      );
    }

    final logs = await DatabaseService.getCompletionLogs(limit: 500);
    for (int i = 0; i < logs.length; i++) {
      final l = logs[i];
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: i + 1))
          .value = TextCellValue((l['date'] as String?) ?? '');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: i + 1))
          .value = TextCellValue((l['time'] as String?) ?? '');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: i + 1))
          .value = TextCellValue(_translateType((l['activity_type'] as String?) ?? ''));
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: i + 1))
          .value = TextCellValue((l['task'] as String?) ?? '');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 4, rowIndex: i + 1))
          .value = TextCellValue(l['completed'] == 1 ? '완료' : '미완료');
      final stepsDone = l['steps_completed'] ?? 0;
      final stepsTotal = l['steps_total'] ?? 0;
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 5, rowIndex: i + 1))
          .value = TextCellValue('$stepsDone / $stepsTotal');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 6, rowIndex: i + 1))
          .value = TextCellValue(l['needed_help'] == 1 ? '예' : '아니오');
    }

    // 컬럼 너비 자동 (excel 패키지 제한: 수동 설정)
    sheet.setColumnWidth(0, 12);
    sheet.setColumnWidth(1, 8);
    sheet.setColumnWidth(2, 12);
    sheet.setColumnWidth(3, 24);
    sheet.setColumnWidth(4, 10);
    sheet.setColumnWidth(5, 10);
    sheet.setColumnWidth(6, 10);
  }

  // ── 시트 2: 프로필 ──
  static Future<void> _addProfileSheet(Excel excel) async {
    final sheet = excel['프로필'];

    final profile = await DatabaseService.getProfile();
    final ingredients = await DatabaseService.getIngredients();
    final meds = await DatabaseService.getMedicineSchedules();
    final contacts = await DatabaseService.getEmergencyContacts();

    int row = 0;

    void writeRow(String k, String v) {
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row))
          .value = TextCellValue(k);
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row))
          .value = TextCellValue(v);
      row++;
    }

    writeRow('이름', (profile['name'] as String?) ?? '');
    writeRow('장애 수준', (profile['disability_level'] as String?) ?? '');
    writeRow('UI 모드', (profile['ui_mode'] as String?) ?? '');
    writeRow('', '');

    // 약
    writeRow('약 알림', '');
    for (final m in meds) {
      writeRow('  - ${m['name']}', '${m['time']} (${m['days']})');
    }
    writeRow('', '');

    // 연락처
    writeRow('긴급 연락처', '');
    for (final c in contacts) {
      writeRow('  - ${c['name']}', '${c['phone']} (${c['relationship']})');
    }
    writeRow('', '');

    // 재료
    writeRow('냉장고 재료', ingredients.map((i) => i['name']).join(', '));

    sheet.setColumnWidth(0, 20);
    sheet.setColumnWidth(1, 30);
  }

  // ── 시트 3: 이번 주 요약 ──
  static Future<void> _addWeeklySummarySheet(Excel excel) async {
    final sheet = excel['이번 주 요약'];

    final now = DateTime.now();
    final weekStart = now.subtract(Duration(days: now.weekday - 1));
    final weekEnd = weekStart.add(const Duration(days: 6));
    final fmt = DateFormat('yyyy-MM-dd');

    final allLogs = await DatabaseService.getCompletionLogs(limit: 500);
    final weekLogs = allLogs.where((l) {
      final d = DateTime.tryParse((l['date'] as String?) ?? '');
      if (d == null) return false;
      return d.isAfter(weekStart.subtract(const Duration(days: 1))) &&
          d.isBefore(weekEnd.add(const Duration(days: 1)));
    }).toList();

    int row = 0;
    void writeRow(List<String> cells, {bool bold = false}) {
      for (int i = 0; i < cells.length; i++) {
        final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: row));
        cell.value = TextCellValue(cells[i]);
        if (bold) cell.cellStyle = CellStyle(bold: true);
      }
      row++;
    }

    writeRow(['하루메이트 주간 요약'], bold: true);
    writeRow(['기간', '${fmt.format(weekStart)} ~ ${fmt.format(weekEnd)}']);
    writeRow(['']);

    // 활동 유형별 집계
    final byType = <String, Map<String, int>>{};
    for (final l in weekLogs) {
      final type = (l['activity_type'] as String?) ?? 'GENERAL';
      byType.putIfAbsent(type, () => {'total': 0, 'done': 0});
      byType[type]!['total'] = byType[type]!['total']! + 1;
      if (l['completed'] == 1) {
        byType[type]!['done'] = byType[type]!['done']! + 1;
      }
    }

    writeRow(['활동 유형', '완료', '전체', '완료율'], bold: true);
    byType.forEach((type, stats) {
      final total = stats['total']!;
      final done = stats['done']!;
      final rate = total > 0 ? '${(done * 100 / total).round()}%' : '-';
      writeRow([_translateType(type), done.toString(), total.toString(), rate]);
    });

    writeRow(['']);
    final totalAll = weekLogs.length;
    final doneAll = weekLogs.where((l) => l['completed'] == 1).length;
    writeRow([
      '전체 수행률',
      '$doneAll / $totalAll',
      '',
      totalAll > 0 ? '${(doneAll * 100 / totalAll).round()}%' : '-'
    ], bold: true);

    sheet.setColumnWidth(0, 20);
    sheet.setColumnWidth(1, 12);
    sheet.setColumnWidth(2, 12);
    sheet.setColumnWidth(3, 10);
  }

  static String _translateType(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
        return '요리';
      case 'MEAL':
        return '식사';
      case 'HEALTH':
        return '운동';
      case 'CLOTHING':
        return '옷 입기';
      case 'LEISURE':
        return '여가';
      case 'MORNING_BRIEFING':
        return '아침 안내';
      case 'NIGHT_WRAPUP':
        return '저녁 마무리';
      case 'REST':
        return '쉬는 시간';
      case 'ROUTINE':
        return '생활 루틴';
      default:
        return '기타';
    }
  }
}
