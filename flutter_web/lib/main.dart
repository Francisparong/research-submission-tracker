import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// Week 14 educational demo. NEVER embed account passwords or API secrets in web assets.
const apiBase = String.fromEnvironment('TRACKER_API_BASE', defaultValue: 'http://127.0.0.1:8091');
void main() => runApp(const TrackerApp());
class TrackerApp extends StatelessWidget {
  const TrackerApp({super.key});
  @override Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Research Submission Tracker | Week 14',
    theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
    home: const TrackerPage(),
  );
}
class TrackerPage extends StatefulWidget {const TrackerPage({super.key});@override State<TrackerPage> createState()=>_TrackerPageState();}
class _TrackerPageState extends State<TrackerPage> {
 final username=TextEditingController(text:'student'),password=TextEditingController(),title=TextEditingController(),student=TextEditingController(),reviewer=TextEditingController(text:'Demo Reviewer'),deadline=TextEditingController(text:'2026-11-20');
 String? token,role; String message='Please log in';bool loading=false;List<dynamic> items=[];Map<String,dynamic> summary={};int? selected;
 @override void dispose(){username.dispose();password.dispose();title.dispose();student.dispose();reviewer.dispose();deadline.dispose();super.dispose();}
 Future<dynamic> api(String path,{Map<String,dynamic>? body,String? authOverride}) async {
  final headers={'Content-Type':'application/json',if(authOverride!=null)'Authorization':'Bearer $authOverride' else if(token!=null)'Authorization':'Bearer $token'};
  final url=Uri.parse('$apiBase$path');
  final response=await (body==null?http.get(url,headers:headers):http.post(url,headers:headers,body:jsonEncode(body))).timeout(const Duration(seconds:8));
  final data=jsonDecode(response.body);
  if(response.statusCode>=400)throw Exception('HTTP ${response.statusCode}: ${data is Map?data['error']:'Request failed'}');
  return data;
 }
 Future<void> login() async {
  setState(()=>loading=true);
  try {
   final result=await api('/login',body:{'username':username.text.trim(),'password':password.text});
   if(!mounted)return;
   setState((){token=result['token'] as String;role=result['role'] as String;message='Login successful: $role';password.clear();});
   await refresh();
  }catch(e){if(mounted)setState(()=>message='Login rejected: $e');}
  finally{if(mounted)setState(()=>loading=false);}
 }
 Future<void> logout() async {
  final current=token;
  if(current!=null){try{await api('/logout',body:{},authOverride:current);}catch(_){}}
  if(mounted)setState((){token=null;role=null;items=[];summary={};selected=null;message='Logged out';});
 }
 Future<void> refresh() async {
  if(token==null)return;
  setState(()=>loading=true);
  try{
   final list=await api('/submissions');final report=await api('/summary');
   if(mounted)setState((){items=list as List<dynamic>;summary=report as Map<String,dynamic>;message='Data loaded (authorized session)';});
  }catch(e){if(mounted)setState(()=>message='API error: $e');}
  finally{if(mounted)setState(()=>loading=false);}
 }
 Future<void> act(String path,Map<String,dynamic> payload) async {
  if(token==null)return;
  setState((){loading=true;message='Processing...';});
  String resultMessage='';
  try {final result=await api(path,body:payload);resultMessage='Success: ${jsonEncode(result)}';}
  catch(e){resultMessage='Request rejected: $e';}
  if(mounted)setState(()=>message=resultMessage);
  // Preserve the last action result; do not overwrite it with refresh's success notice.
  try {final a=await api('/submissions'),b=await api('/summary');if(mounted)setState((){items=a as List<dynamic>;summary=b as Map<String,dynamic>;});}catch(_){ }
  if(mounted)setState(()=>loading=false);
 }
 @override Widget build(BuildContext context) => Scaffold(
  appBar:AppBar(title:const Text('Research Submission Tracker | Week 14',maxLines:2,overflow:TextOverflow.ellipsis)),
  body:Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:900),child:ListView(padding:const EdgeInsets.all(16),children:[
   const Text('Controlled demo data • No credentials stored in Flutter source • Local testing only',style:TextStyle(fontWeight:FontWeight.bold)),
   const SizedBox(height:8),Text('API: $apiBase',style:const TextStyle(fontSize:12)),
   if(token==null)...[
    const SizedBox(height:18),const Text('1. Login with local test credentials',style:TextStyle(fontWeight:FontWeight.bold)),
    DropdownButtonFormField<String>(initialValue:username.text,items:const [DropdownMenuItem(value:'student',child:Text('student')),DropdownMenuItem(value:'staff',child:Text('staff'))],onChanged:(s)=>username.text=s??'student',decoration:const InputDecoration(labelText:'User')),
    TextField(controller:password,obscureText:true,enableSuggestions:false,autocorrect:false,decoration:const InputDecoration(labelText:'Password (local only)')),
    FilledButton(onPressed:loading?null:login,child:const Text('Log in')),
   ]else...[
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[Flexible(child:Text('Signed in as $role')),OutlinedButton(onPressed:loading?null:logout,child:const Text('Log out'))]),
    const Divider(),Text('Summary: ${jsonEncode(summary)}'),
    const SizedBox(height:12),const Text('2. Create research submission (student only)',style:TextStyle(fontWeight:FontWeight.bold)),
    TextField(controller:title,maxLength:150,decoration:const InputDecoration(labelText:'Research title')),
    TextField(controller:student,maxLength:100,decoration:const InputDecoration(labelText:'Fictional student name')),
    FilledButton(onPressed:loading?null:()=>act('/submissions',{'title':title.text,'student':student.text}),child:const Text('Submit')),
    const Divider(),const Text('3. Review, revision and automation',style:TextStyle(fontWeight:FontWeight.bold)),
    if(items.isEmpty)const Text('No submissions yet.'),
    ...items.map((e)=>RadioListTile<int>(value:e['id'] as int,groupValue:selected,onChanged:(v)=>setState(()=>selected=v),title:Text('#${e['id']} ${e['title']} | v${e['version']}'),subtitle:Text('Status: ${e['status']} • Reviewer: ${e['reviewer'] ?? 'unassigned'} • Due: ${e['deadline'] ?? 'none'}'))),
    TextField(controller:reviewer,decoration:const InputDecoration(labelText:'Reviewer (fictional)')),
    TextField(controller:deadline,decoration:const InputDecoration(labelText:'Deadline YYYY-MM-DD')),
    Wrap(spacing:8,runSpacing:4,children:[
     OutlinedButton(onPressed:selected==null||loading?null:()=>act('/assign',{'id':selected,'reviewer':reviewer.text,'deadline':deadline.text}),child:const Text('Assign reviewer (staff)')),
     OutlinedButton(onPressed:selected==null||loading?null:()=>act('/revision',{'id':selected}),child:const Text('Submit revision (student)')),
     OutlinedButton(onPressed:selected==null||loading?null:()=>act('/automation/run',{'id':selected,'simulate':'none'}),child:const Text('Run reminder (staff)')),
    ]),
    OutlinedButton(onPressed:loading?null:refresh,child:const Text('Refresh summary')),
   ],
   const Divider(),Text('Status: $message',key:const Key('statusMessage')),
   if(loading)const LinearProgressIndicator(),
   const SizedBox(height:8),const Text('Security limits: Browser session token is held in memory only, not localStorage. API requires TLS for any non-local network; never use real student records.'),
  ]))),
 );
}
