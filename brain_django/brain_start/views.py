from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import os
import json
import logging
import re
import uuid
from datetime import datetime
import pandas as pd
from django.utils import timezone
# 添加对 EEGAnalyzer 的导入
from .eeg_analyzer import EEGAnalyzer
from .models import EEGDataPoint, EEGRecord

logger = logging.getLogger(__name__)

def runoob(request):
    context = {}
    context['hello'] = 'Hello World!'
    return render(request, 'runoob.html', context)
def eeg(request):
    context = {}
    context['hello'] = 'EEG Page!'
    return render(request, 'EEG.html', context)


def serve_report(request, filename):
    """提供报告访问"""
    try:
        report_file = os.path.join("analysis_reports", filename)
        if not os.path.exists(report_file):
            return JsonResponse({'error': '报告不存在'}, status=404)

        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HttpResponse(content, content_type='text/html; charset=utf-8')

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




# @csrf_exempt
# def import_eeg_data(request):
#     """处理导入的EEG数据"""
#     if request.method != 'POST':
#         return JsonResponse({'status': 'error', 'message': '只支持POST请求'}, status=400)
    
#     try:
#         # 确保日志目录存在
#         log_dir = "logs"
#         if not os.path.exists(log_dir):
#         os.makedirs(log_dir)
        
#         # 生成日志文件名
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         log_file = os.path.join(log_dir, f"imported_eeg_data_{timestamp}.txt")
        
#         # 获取API密钥（如果提供了的话）
#         api_key = "51e09aa5-d2dd-41ab-bf91-51ef798844e7"
#         if request.content_type == 'application/json':
#             try:
#                 json_data = json.loads(request.body)
#                 api_key = json_data.get('api_key', api_key)
#             except:
#                 pass
        
#         # 获取上传的文件
#         if 'file' in request.FILES:
#             uploaded_file = request.FILES['file']
            
#             # 根据文件扩展名处理
#             if uploaded_file.name.endswith(('.csv', '.txt')):
#                 # CSV/文本文件处理
#                 try:
#                     # 尝试以UTF-8编码读取
#                     file_content = uploaded_file.read().decode('utf-8')
#                 except UnicodeDecodeError:
#                     # 如果UTF-8失败，尝试以GBK编码读取
#                     uploaded_file.seek(0)  # 重置文件指针
#                     file_content = uploaded_file.read().decode('gbk')
                
#                 with open(log_file, 'w', encoding='utf-8') as f:
#                     f.write(file_content)
#                 message = f"成功导入文本文件: {uploaded_file.name}"
                
#             elif uploaded_file.name.endswith(('.xls', '.xlsx')):
#                 # Excel文件处理
#                 try:
#                     # 读取Excel文件
#                     df = pd.read_excel(uploaded_file)
                    
#                     # 转换为文本格式保存
#                     with open(log_file, 'w', encoding='utf-8') as f:
#                         # 将DataFrame转换为文本格式
#                         for index, row in df.iterrows():
#                             timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
#                             # 查找包含脑电波频段的列
#                             delta_col = None
#                             theta_col = None
#                             alpha_col = None
#                             beta_col = None
#                             gamma_col = None
                            
#                             # 查找精确匹配的列名
#                             for col in df.columns:
#                                 col_lower = str(col).lower()
#                                 if 'delta' in col_lower:
#                                     delta_col = col
#                                 elif 'theta' in col_lower:
#                                     theta_col = col
#                                 elif 'alpha' in col_lower:
#                                     alpha_col = col
#                                 elif 'beta' in col_lower:
#                                     beta_col = col
#                                 elif 'gamma' in col_lower:
#                                     gamma_col = col
                            
#                             # 如果找到了所有需要的列
#                             if all([delta_col, theta_col, alpha_col, beta_col, gamma_col]):
#                                 data_str = f"Delta {row[delta_col]} Theta {row[theta_col]} Alpha {row[alpha_col]} Beta {row[beta_col]} Gamma {row[gamma_col]}"
#                                 f.write(f"{timestamp} - {data_str}\n")
#                             else:
#                                 # 尝试使用默认列名
#                                 if all(col in df.columns for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']):
#                                     data_str = f"Delta {row['Delta']} Theta {row['Theta']} Alpha {row['Alpha']} Beta {row['Beta']} Gamma {row['Gamma']}"
#                                     f.write(f"{timestamp} - {data_str}\n")
#                                 else:
#                                     # 如果还是找不到合适的列，将整行转换为字符串
#                                     f.write(f"{timestamp} - {row.to_string()}\n")
                    
#                     message = f"成功导入Excel文件: {uploaded_file.name}"
#                 except Exception as e:
#                     logger.error(f"Excel文件处理失败: {str(e)}")
#                     # 如果处理失败，保存原始文件内容
#                     uploaded_file.seek(0)
#                     file_content = uploaded_file.read().decode('utf-8', errors='ignore')
#                     with open(log_file, 'w', encoding='utf-8') as f:
#                         f.write(file_content)
#                     message = f"导入Excel文件时出现错误，已保存原始内容: {uploaded_file.name}"
#             else:
#                 # 其他文件类型直接保存
#                 file_content = uploaded_file.read().decode('utf-8', errors='ignore')
#                 with open(log_file, 'w', encoding='utf-8') as f:
#                     f.write(file_content)
#                 message = f"成功导入文件: {uploaded_file.name}"
#         else:
#             # 从请求体获取数据
#             try:
#                 data = json.loads(request.body)
#                 api_key = data.get('api_key', api_key)
#                 with open(log_file, 'w', encoding='utf-8') as f:
#                     f.write(json.dumps(data, ensure_ascii=False, indent=2))
#                 message = "成功导入JSON数据"
#             except json.JSONDecodeError:
#                 # 如果不是JSON数据，直接保存
#                 with open(log_file, 'wb') as f:
#                     f.write(request.body)
#                 message = "成功导入原始数据"
        
#         # 只保存数据，不立即进行分析
#         return JsonResponse({
#             'status': 'success', 
#             'message': message,
#             'file_path': log_file
#         })
        
#     except Exception as e:
#         logger.error(f"导入数据失败: {str(e)}")
#         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
@csrf_exempt
def import_eeg_data(request):
    """处理导入的EEG数据"""
    logger.info("Import EEG data function called")
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只支持POST请求'}, status=400)
    
    try:
        # 获取API密钥（如果提供了的话）
        
        if request.content_type == 'application/json':
            try:
                json_data = json.loads(request.body)
                api_key = json_data.get('api_key', api_key)
            except:
                pass
        else :
            api_key = "51e09aa5-d2dd-41ab-bf91-51ef798844e7"
        # 获取上传的文件
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            
            # 根据文件扩展名处理
            if uploaded_file.name.endswith(('.csv', '.txt')):
                # CSV/文本文件处理
                try:
                    # 尝试以UTF-8编码读取
                    file_content = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    # 如果UTF-8失败，尝试以GBK编码读取
                    uploaded_file.seek(0)  # 重置文件指针
                    file_content = uploaded_file.read().decode('gbk')
                
                # 解析并保存数据到数据库
                logging.info("Parsing CSV/Text file")
                saved_count, recording_id = _save_eeg_data_to_db(file_content, uploaded_file.name)
                message = f"成功导入文本文件: {uploaded_file.name}，已保存 {saved_count} 条记录到数据库"
                
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                # Excel文件处理
                try:
                    # 读取Excel文件
                    df = pd.read_excel(uploaded_file)
                    
                    # 转换为文本格式并保存到数据库
                    saved_count, recording_id = _save_eeg_excel_data_to_db(df, uploaded_file.name)
                    message = f"成功导入Excel文件: {uploaded_file.name}，已保存 {saved_count} 条记录到数据库"
                except Exception as e:
                    logger.error(f"Excel文件处理失败: {str(e)}")
                    message = f"导入Excel文件时出现错误: {str(e)}"
            else:
                # 其他文件类型尝试解析并保存到数据库
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                saved_count, recording_id = _save_eeg_data_to_db(file_content, uploaded_file.name)
                message = f"成功导入文件: {uploaded_file.name}，已保存 {saved_count} 条记录到数据库"
        else:
            # 从请求体获取数据
            try:
                data = json.loads(request.body)
                api_key = data.get('api_key', api_key)
                # 将JSON数据保存到数据库
                saved_count, recording_id = _save_eeg_json_data_to_db(data)
                message = f"成功导入JSON数据，已保存 {saved_count} 条记录到数据库"
            except json.JSONDecodeError:
                # 如果不是JSON数据，直接保存
                saved_count = 0
                recording_id = None
                message = "成功导入原始数据"
        
        response_data = {
            'status': 'success', 
            'message': message
        }
        
        if recording_id:
            response_data['recording_id'] = recording_id
            
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"导入数据失败: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def _save_eeg_data_to_db(file_content, file_name=None):
    """将EEG数据保存到数据库"""
    from django.utils import timezone
    logging.info("Saving EEG data to database")
    lines = file_content.strip().split('\n')
    saved_count = 0
    
    if not lines:
        return saved_count, None
         
    # 解析第一行和最后一行的时间，用于创建EEGRecord
    first_timestamp = None
    last_timestamp = None
    
    try:
        first_timestamp_str, _ = lines[0].strip().split(' - ', 1)
        first_timestamp = timezone.make_aware(datetime.strptime(first_timestamp_str, '%Y-%m-%d %H:%M:%S'))
    except (ValueError, IndexError):
        first_timestamp = timezone.now()
        
    try:
        last_timestamp_str, _ = lines[-1].strip().split(' - ', 1)
        last_timestamp = timezone.make_aware(datetime.strptime(last_timestamp_str, '%Y-%m-%d %H:%M:%S'))
    except (ValueError, IndexError):
        last_timestamp = timezone.now()
    
 
    
    eeg_record = EEGRecord(
        
        start_time=first_timestamp,
        end_time=last_timestamp,
        name=file_name or 'EEG_Recording',
        description=f'从文件导入的EEG数据: {file_name}',
        data_count=len(lines)
    )
    recording_id = eeg_record.recording_id
    eeg_record.save()
    
    # 保存数据点
    with transaction.atomic():
        for line in lines:
            if ' - ' not in line:
                continue
                
            try:
                # 解析时间戳和数据
                timestamp_str, raw_data = line.strip().split(' - ', 1)
                # 尝试解析时间戳
                try:
                    timestamp = timezone.make_aware(datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    timestamp = timezone.now()
                
                # 解析脑电波数据
                eeg_data = _parse_eeg_data(raw_data)
                logger.info(f"EEG Data: ")
                # 创建并保存EEGDataPoint对象
                eeg_data_point = EEGDataPoint(
                    recording=eeg_record,
                    time=timestamp,
                    delta=eeg_data.get('Delta', 0),
                    theta=eeg_data.get('Theta', 0),
                    low_alpha=eeg_data.get('LowAlpha', 0),
                    low_beta=eeg_data.get('LowBeta', 0),
                    low_gamma=eeg_data.get('LowGamma', 0),
                    high_alpha=eeg_data.get('HighAlpha', 0),
                    high_beta=eeg_data.get('HighBeta', 0),
                    high_gamma=eeg_data.get('HighGamma', 0),
                    attention=eeg_data.get('Attention', 0),
                    meditation=eeg_data.get('Meditation', 0),
                    signal_quality=eeg_data.get('SignalQuality', 0)
                )
                eeg_data_point.save()
                saved_count += 1
            except Exception as e:
                logger.error(f"解析并保存数据行失败: {line}, 错误: {str(e)}")
                continue
    
    return saved_count, recording_id

def _save_eeg_excel_data_to_db(df, file_name=None):
    """将Excel格式的EEG数据保存到数据库"""
    from django.utils import timezone
    
    saved_count = 0
    
    if df.empty:
        return saved_count, None
        
    # 获取第一行和最后一行的时间
    first_timestamp = timezone.now()
    last_timestamp = timezone.now()
    
    eeg_record = EEGRecord(
        start_time=first_timestamp,
        end_time=last_timestamp,
        name=file_name or 'EEG_Recording',
        description=f'从Excel文件导入的EEG数据: {file_name}',
        data_count=len(df)
    )
    eeg_record.save()
    recording_id = eeg_record.recording_id
    
    # 转换为文本格式并保存到数据库
    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                timestamp = timezone.now()
                
                # 查找包含脑电波频段的列
                delta_val = theta_val = alpha_val = beta_val = gamma_val = 0.0
                
                # 查找精确匹配的列名
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'delta' in col_lower:
                        delta_val = float(row[col])
                    elif 'theta' in col_lower:
                        theta_val = float(row[col])
                    elif 'alpha' in col_lower and 'low' in col_lower:
                        alpha_val = float(row[col])
                    elif 'beta' in col_lower and 'low' in col_lower:
                        beta_val = float(row[col])
                    elif 'gamma' in col_lower and 'low' in col_lower:
                        gamma_val = float(row[col])
                
                # 创建并保存EEGDataPoint对象
                eeg_data_point = EEGDataPoint(
                    recording=eeg_record,
                    time=timestamp,
                    delta=delta_val,
                    theta=theta_val,
                    low_alpha=alpha_val,
                    low_beta=beta_val,
                    low_gamma=gamma_val
                )
                eeg_data_point.save()
                saved_count += 1
            except Exception as e:
                logger.error(f"保存Excel数据行失败: {index}, 错误: {str(e)}")
                continue
                
    return saved_count, recording_id




""""
准备弃用
"""
def latest_eeg_record(request):
    """
    显示最新的 EEGRecord 记录
    """
    try:
        latest_record = EEGRecord.objects.latest('start_time')
        data_points = latest_record.data_points.all()
        
        context = {
            'record': latest_record,
            'data_points': data_points,
        }
        return render(request, 'latest_eeg_record.html', context)
    except EEGRecord.DoesNotExist:
        return render(request, 'no_record.html')






def _parse_eeg_data(raw_data):
    """解析原始EEG数据字符串"""
    # 匹配类似 "Delta 10 Theta 20 Alpha 30" 的格式
    eeg_data = {}
    pattern = r'(\w+)\s+(\d+\.?\d*)'
    matches = re.findall(pattern, raw_data)
    
    for key, value in matches:
        eeg_data[key] = float(value)
    
    return eeg_data


def _save_eeg_json_data_to_db(json_data):
    """将JSON格式的EEG数据保存到数据库"""
    from django.utils import timezone
    
    # 如果是数组，逐个处理
    data_list = json_data if isinstance(json_data, list) else [json_data]
    saved_count = 0
    
    if not data_list:
        return saved_count, None
        
    eeg_record = EEGRecord(
        start_time=timezone.now(),
        end_time=timezone.now(),
        name='JSON导入的EEG数据',
        description='从JSON数据导入的EEG记录',
        data_count=len(data_list)
    )
    eeg_record.save()
    recording_id = eeg_record.recording_id
    
    with transaction.atomic():
        for data in data_list:
            try:
                eeg_data_point = EEGDataPoint(
                    recording=eeg_record,
                    time=timezone.now(),
                    delta=data.get('delta', 0),
                    theta=data.get('theta', 0),
                    low_alpha=data.get('low_alpha', 0),
                    low_beta=data.get('low_beta', 0),
                    low_gamma=data.get('low_gamma', 0),
                    high_alpha=data.get('high_alpha', 0),
                    high_beta=data.get('high_beta', 0),
                    high_gamma=data.get('high_gamma', 0),
                    attention=data.get('attention', 0),
                    meditation=data.get('meditation', 0),
                    signal_quality=data.get('signal_quality', 0)
                )
                eeg_data_point.save()
                saved_count += 1
            except Exception as e:
                logger.error(f"保存JSON数据失败: {str(e)}")
                continue
    
    return saved_count, recording_id

    """待修改

      从数据库分析
    """
 
@csrf_exempt
def analyze_existing_data(request):
    """分析已有的数据文件"""
    logger.info(f"收到分析请求: {request.method}")
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只支持POST请求'}, status=400)
    
    try:
        data = json.loads(request.body)
        recording_id = data.get('recording_id')
        api_key = data.get('api_key', '51e09aa5-d2dd-41ab-bf91-51ef798844e7')
        
        if not recording_id:
            return JsonResponse({'status': 'error', 'message': '缺少 recording_id 参数'}, status=400)
        
        # 验证recording_id格式
        try:
            uuid.UUID(str(recording_id))
        except ValueError:
            return JsonResponse({'status': 'error', 'message': '无效的 recording_id 格式'}, status=400)
        
        # 从数据库获取记录并生成临时文件
        from .models import EEGRecord, EEGDataPoint
        import tempfile
        import os
        from django.conf import settings
        
        record = EEGRecord.objects.get(recording_id=recording_id)
        data_points = EEGDataPoint.objects.filter(recording=record).order_by('time')
        
        if not data_points.exists():
            return JsonResponse({'status': 'error', 'message': '指定的记录没有数据'}, status=400)
        
        # 创建临时文件
        temp_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f'temp_analysis_data_{recording_id}.txt')
        
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            for point in data_points:
                line = f"{point.time.strftime('%Y-%m-%d %H:%M:%S')} - Delta {point.delta} Theta {point.theta} LowAlpha {point.low_alpha} HighAlpha {point.high_alpha} LowBeta {point.low_beta} HighBeta {point.high_beta} LowGamma {point.low_gamma} HighGamma {point.high_gamma} Attention {point.attention} Meditation {point.meditation} SignalQuality {point.signal_quality}\n"
                f.write(line)
        
        file_path = temp_file_path
        
        # 执行分析
        analyzer = EEGAnalyzer(file_path, api_key)
        result = analyzer.analyze()
        
        # 删除临时文件
        if 'temp_analysis_data_' in file_path:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")
        
        # 返回分析结果（包含报告内容）
        if isinstance(result, dict):
            if result.get('status') == 'error':
                return JsonResponse(result, status=400 if '不存在' in result.get('message', '') else 500)
            else:
                # 如果result包含报告内容，直接返回
                if 'report_content' in result:
                    return JsonResponse({
                        'status': 'success',
                        'report_content': result['report_content'],
                        'report_filename': result.get('report_filename'),
                        'message': result.get('message', '分析完成')
                    })
                else:
                    # 否则返回报告文件名，让前端去获取
                    return JsonResponse({
                        'status': 'success',
                        'report_filename': result.get('report_filename'),
                        'message': result.get('message', '分析完成')
                    })
        else:
            # 兼容旧版本返回元组的情况
            report_content, report_filename = result
            return JsonResponse({
                'status': 'success',
                'report_content': report_content,
                'report_filename': report_filename,
                'message': '分析完成'
            })
        
    except json.JSONDecodeError as e:
        return JsonResponse({'status': 'error', 'message': '请求数据格式错误'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
 
#  新增API接口：获取最新的EEG记录
@csrf_exempt
def latest_eeg_record_json(request):
    """
    返回最新的 EEGRecord 记录（JSON格式）
    """
    try:
        latest_record = EEGRecord.objects.latest('start_time')
        data = {
            'recording_id': latest_record.recording_id,
            'start_time': latest_record.start_time.isoformat(),
            'end_time': latest_record.end_time.isoformat(),
            'name': latest_record.name,
            'description': latest_record.description,
            'data_count': latest_record.data_count
        }
        return JsonResponse(data)
    except EEGRecord.DoesNotExist:
        return JsonResponse({'error': 'No records found'}, status=404)

#  新增API接口：获取所有EEG记录
@csrf_exempt
def all_eeg_records_json(request):
    """
    返回所有 EEGRecord 记录（JSON格式）
    """
    try:
        records = EEGRecord.objects.all().order_by('-start_time')
        data = []
        for record in records:
            data.append({
                'recording_id': record.recording_id,
                'start_time': record.start_time.isoformat(),
                'end_time': record.end_time.isoformat(),
                'name': record.name,
                'description': record.description,
                'data_count': record.data_count
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
def test_api_key(request):
    """测试API密钥有效性"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只支持POST请求'}, status=400)
    
    try:
        data = json.loads(request.body)
        api_key = data.get('api_key', '')
        
        if not api_key:
            return JsonResponse({'status': 'error', 'message': 'API密钥不能为空'}, status=400)
        
        # 使用一个简单的测试提示来验证API密钥
        analyzer = EEGAnalyzer("", api_key)
        test_prompt = "请回复'测试成功'这四个字，不要包含其他内容。"
        
        # 尝试调用API
        response = analyzer.call_volcengine_api(api_key, test_prompt, "doubao-seed-1-6-lite-251015")  # 使用较轻量的模型进行测试
        
        # 检查响应是否包含错误
        if "火山引擎API调用失败" in response:
            return JsonResponse({'status': 'error', 'message': 'API密钥无效或连接失败'}, status=400)
        
        return JsonResponse({'status': 'success', 'message': 'API密钥验证成功'})
        
    except Exception as e:
        logger.error(f"API密钥测试失败: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'测试失败: {str(e)}'}, status=500)