import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const TrackerApp());
class TrackerApp extends StatelessWidget {
  const TrackerApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(title: 'Research Submission Tracker', theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true), home: const TrackerPage());
}
class TrackerPage extends StatefulWidget { const TrackerPage({super.key}); @override State<TrackerPage> createState() => _TrackerPageState(); }
class _TrackerPageState extends State<TrackerPage> {
  final title = TextEditingController(), student = TextEditingController(), reviewer = TextEditingController(text: 'Demo Reviewer'), deadline = TextEditingController(text: '2026-10-20');
  String role='student', message='Ready'; bool loading=false; List<dynamic> items=[]; Map<String,dynamic> summary={}; int? selected;
  final String base='http://127.0.0.1:8091';
  @override void initState(){super.initState();refresh();}
  Future<dynamic> api(String path,{Map<String,dynamic>? body}) async {
    final headers={'Content-Type':'application/json','X-Demo-Role':role};
    final uri=Uri.parse('$base$path');
    final response=body==null ? await http.get(uri,headers:headers) : await http.post(uri,headers:headers,body:jsonEncode(body));
    final data=jsonDecode(response.body);
    if(response.statusCode>=400) throw Exception(data['error'] ?? 'HTTP ${response.statusCode}');
    return data;
  }
  Future<void> refresh() async {
    setState((){loading=true;});
    try {final a=await api('/submissions'), b=await api('/summary'); if(mounted)setState((){items=a;summary=b;message='Data loaded';});}
    catch(e){if(mounted)setState((){message='Network/server error: $e';});}
    finally{if(mounted)setState((){loading=false;});}
  }
  Future<void> act(String path,Map<String,dynamic> body) async {
    setState((){loading=true;message='Processing...';});
    try{final result=await api(path,body:body); if(mounted)setState((){message='Success: ${jsonEncode(result)}';});await refresh();}
    catch(e){if(mounted)setState((){message='Validation/authorization/server error: $e';});}
    finally{if(mounted)setState((){loading=false;});}
  }
  @override Widget build(BuildContext context) => Scaffold(
    appBar:AppBar(title:const Text('Research Submission Tracker | Week 13')),
    body:Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:950),child:ListView(padding:const EdgeInsets.all(20),children:[
      const Text('Controlled demo data only • Week 13: simulated notification delivery',style:TextStyle(fontWeight:FontWeight.bold)),
      const SizedBox(height:12),
      DropdownButton<String>(value:role,items:['student','staff'].map((s)=>DropdownMenuItem(value:s,child:Text('Demo role: $s'))).toList(),onChanged:(v)=>setState(()=>role=v!)),
      Text('Status: $message'), if(loading)const LinearProgressIndicator(),
      const SizedBox(height:12),Text('Summary: ${jsonEncode(summary)}'),
      const Divider(),const Text('1. Create a submission (student)',style:TextStyle(fontWeight:FontWeight.bold)),
      TextField(controller:title,decoration:const InputDecoration(labelText:'Research title')),
      TextField(controller:student,decoration:const InputDecoration(labelText:'Student (fictional name)')),
      FilledButton(onPressed:loading?null:()=>act('/submissions',{'title':title.text,'student':student.text}),child:const Text('Submit')),
      const Divider(),const Text('2. Select submission, assign reviewer, revise or run automation',style:TextStyle(fontWeight:FontWeight.bold)),
      if(items.isEmpty)const Text('No submissions yet (empty state).'),
      ...items.map((e)=>RadioListTile<int>(value:e['id'] as int,groupValue:selected,onChanged:(v)=>setState(()=>selected=v),title:Text('#${e['id']} ${e['title']} | v${e['version']}'),subtitle:Text('Status: ${e['status']} | Reviewer: ${e['reviewer'] ?? 'unassigned'} | Deadline: ${e['deadline'] ?? 'none'}'))),
      TextField(controller:reviewer,decoration:const InputDecoration(labelText:'Reviewer (fictional)')),
      TextField(controller:deadline,decoration:const InputDecoration(labelText:'Deadline YYYY-MM-DD')),
      Wrap(spacing:8,children:[
        OutlinedButton(onPressed:selected==null||loading?null:()=>act('/assign',{'id':selected,'reviewer':reviewer.text,'deadline':deadline.text}),child:const Text('Assign reviewer (staff)')),
        OutlinedButton(onPressed:selected==null||loading?null:()=>act('/revision',{'id':selected}),child:const Text('Submit revised version (student)')),
        OutlinedButton(onPressed:selected==null||loading?null:()=>act('/automation/run',{'id':selected,'simulate':'none'}),child:const Text('Normal reminder (staff)')),
        OutlinedButton(onPressed:selected==null||loading?null:()=>act('/automation/run',{'id':selected,'simulate':'transient'}),child:const Text('Recover transient failure (staff)')),
        OutlinedButton(onPressed:selected==null||loading?null:()=>act('/automation/run',{'id':selected,'simulate':'permanent'}),child:const Text('Route permanent failure (staff)')),
      ]),
      const Divider(),OutlinedButton(onPressed:refresh,child:const Text('Refresh / Show summary')),
      const Text('Important: role selector is a Week 13 demonstration only. Real authentication, access control, HTTPS and configuration protection belong to Week 14.'),
    ]))),
  );
}
