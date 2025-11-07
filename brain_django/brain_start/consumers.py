import json
import os
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from .eeg_analyzer import EEGAnalyzer
import asyncio
import uuid
from django.db.models import Max

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局日志文件管理
current_log_file = None
LOG_DIR = "logs"
ANALYSIS_DIR = "analysis_reports"
DEFAULT_API_KEY = "51e09aa5-d2dd-41ab-bf91-51ef798844e7"

# 全局变量用于跟踪记录状态
current_recording = None
recording_lock = asyncio.Lock()


def init_log_file():
    """初始化日志文件"""
    global current_log_file
    # 确保日志目录存在
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    current_log_file = os.path.join(LOG_DIR, f"eeg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")


def create_new_log_file():
    """创建新日志文件"""
    global current_log_file
    # 确保日志目录存在
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    new_file = os.path.join(LOG_DIR, f"eeg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    current_log_file = new_file
    return new_file


# 初始化日志文件
init_log_file()


class EEGDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # 根据消息类型处理不同事件
            if 'type' in data:
                if data['type'] == 'eeg_data':
                    await self.handle_eeg_data(data)
                elif data['type'] == 'request_analysis':
                    await self.handle_analysis_request(data)
                elif data['type'] == 'imported_data':
                    await self.handle_imported_data(data)
                elif data['type'] == 'start_recording':
                    await self.start_recording(data)
                elif data['type'] == 'stop_recording':
                    await self.stop_recording(data)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_eeg_data(self, data):
        """处理EEG数据"""
        try:
            global current_log_file, current_recording

            # 日志文件轮换（5MB）
            if not os.path.exists(current_log_file) or os.path.getsize(current_log_file) > 1024 * 1024 * 5:
                create_new_log_file()

            # 写入数据，格式化为与分析器兼容的格式
            eeg_data = data.get('data', {})
            if isinstance(eeg_data, dict):
                # 处理字典格式数据
                formatted_data = f"Delta {eeg_data.get('Delta', 0)} Theta {eeg_data.get('Theta', 0)} Alpha {eeg_data.get('Alpha', 0)} Beta {eeg_data.get('Beta', 0)} Gamma {eeg_data.get('Gamma', 0)}"
                # 提取各波段数值用于数据库存储
                delta = eeg_data.get('Delta', 0)
                theta = eeg_data.get('Theta', 0)
                alpha = eeg_data.get('Alpha', 0)
                beta = eeg_data.get('Beta', 0)
                gamma = eeg_data.get('Gamma', 0)
            elif isinstance(eeg_data, str):
                # 处理字符串格式数据（来自蓝牙设备的原始数据）
                # 检查是否为TGAM数据包格式
                if eeg_data.startswith('AA AA'):
                    # 解析TGAM数据包
                    formatted_data = self._parse_tgam_data(eeg_data)
                else:
                    # 直接使用字符串数据
                    formatted_data = eeg_data
                    
                # 从格式化数据中提取各波段数值
                delta, theta, alpha, beta, gamma = self._extract_bands_from_formatted(formatted_data)
            else:
                formatted_data = str(eeg_data)
                delta = theta = alpha = beta = gamma = 0
            
            with open(current_log_file, "a", encoding="utf-8") as f:
                f.write(f"{data['timestamp']} - {formatted_data}\n")
            logger.info(f"写入数据: {data['timestamp']}")
            
            # 添加调试信息
            logger.info(f"current_recording: {current_recording}")
            if current_recording is not None:
                logger.info(f"current_recording.recording_id: {current_recording.recording_id}")
            
            # 如果正在记录，则将数据写入数据库
            if current_recording is not None:
                from django.utils.dateparse import parse_datetime
                from asgiref.sync import sync_to_async
                from django.utils import timezone
                
                # 创建数据点
                timestamp = parse_datetime(data['timestamp'])
                if timestamp is None:
                    timestamp = timezone.now()
                
                # 延迟导入模型以避免Django配置问题
                from .models import EEGDataPoint
                
                # 异步创建数据点
                await sync_to_async(EEGDataPoint.objects.create)(
                    recording=current_recording,
                    time=timestamp,
                    delta=delta,
                    theta=theta,
                    low_alpha=alpha,
                    low_beta=beta,
                    low_gamma=gamma,
                    high_alpha=alpha,
                    high_beta=beta,
                    high_gamma=gamma,
                    attention=0,  # 注意力和冥想度暂设为0，可以根据需要调整
                    meditation=0,
                    signal_quality=0
                )
                
                # 增加记录的数据点计数
                await self.increment_data_count(current_recording)
            
            # 发送确认消息
            await self.send(text_data=json.dumps({
                'type': 'data_received',
                'timestamp': data['timestamp']
            }))

        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'data_error',
                'error': str(e)
            }))

    def _parse_tgam_data(self, raw_data):
        """
        解析TGAM数据包格式
        根据text1.py中的TGAMDataCollector._parse_packet方法实现
        """
        try:
            # 简化的TGAM数据解析（实际应用中需要更复杂的解析逻辑）
            parts = raw_data.split()
            
            # 查找各个频段的值
            eeg_bands = {
                'Delta': 0,
                'Theta': 0,
                'Alpha': 0,
                'Beta': 0,
                'Gamma': 0
            }
            
            # 解析数据
            for i, part in enumerate(parts):
                if part == 'Delta' and i + 1 < len(parts):
                    eeg_bands['Delta'] = int(parts[i + 1])
                elif part == 'Theta' and i + 1 < len(parts):
                    eeg_bands['Theta'] = int(parts[i + 1])
                elif part == 'Alpha' and i + 1 < len(parts):
                    eeg_bands['Alpha'] = int(parts[i + 1])
                elif part == 'Beta' and i + 1 < len(parts):
                    eeg_bands['Beta'] = int(parts[i + 1])
                elif part == 'Gamma' and i + 1 < len(parts):
                    eeg_bands['Gamma'] = int(parts[i + 1])
            
            # 格式化为标准格式
            return f"Delta {eeg_bands['Delta']} Theta {eeg_bands['Theta']} Alpha {eeg_bands['Alpha']} Beta {eeg_bands['Beta']} Gamma {eeg_bands['Gamma']}"
        except Exception as e:
            logger.error(f"TGAM数据解析失败: {str(e)}")
            return raw_data

    def _extract_bands_from_formatted(self, formatted_data):
        """
        从格式化数据中提取各波段数值
        """
        delta = theta = alpha = beta = gamma = 0
        try:
            parts = formatted_data.split()
            for i, part in enumerate(parts):
                if part == 'Delta' and i + 1 < len(parts):
                    delta = int(parts[i + 1])
                elif part == 'Theta' and i + 1 < len(parts):
                    theta = int(parts[i + 1])
                elif part == 'Alpha' and i + 1 < len(parts):
                    alpha = int(parts[i + 1])
                elif part == 'Beta' and i + 1 < len(parts):
                    beta = int(parts[i + 1])
                elif part == 'Gamma' and i + 1 < len(parts):
                    gamma = int(parts[i + 1])
        except Exception as e:
            logger.error(f"提取波段数据失败: {str(e)}")
        
        return delta, theta, alpha, beta, gamma

    async def start_recording(self, data):
        """开始记录数据到数据库"""
        global current_recording
        
        async with recording_lock:
            if current_recording is not None:
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'already_recording',
                    'message': '已经处于记录状态'
                }))
                return
                
            try:
                # 创建新的EEG记录
                recording_name = data.get('name', f'EEG_Recording_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                recording_description = data.get('description', 'EEG数据记录')
                
                current_recording = await self.create_eeg_record(recording_name, recording_description)
                
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'started',
                    'recording_id': current_recording.recording_id,
                    'message': f'开始记录，记录ID: {current_recording.recording_id}'
                }))
                
            except Exception as e:
                logger.error(f"启动记录失败: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'error',
                    'message': f'启动记录失败: {str(e)}'
                }))

    async def stop_recording(self, data):
        """停止记录数据到数据库"""
        global current_recording
        
        async with recording_lock:
            if current_recording is None:
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'not_recording',
                    'message': '当前没有正在进行的记录'
                }))
                return
                
            try:
                # 更新记录的结束时间
                from django.utils import timezone
                current_recording.end_time = timezone.now()
                await self.update_eeg_record(current_recording)
                
                recording_id = current_recording.recording_id
                current_recording = None
                
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'stopped',
                    'recording_id': recording_id,
                    'message': f'记录已停止，记录ID: {recording_id}'
                }))
                
            except Exception as e:
                logger.error(f"停止记录失败: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'recording_status',
                    'status': 'error',
                    'message': f'停止记录失败: {str(e)}'
                }))

    async def create_eeg_record(self, name, description):
        """创建EEG记录"""
        from django.utils import timezone
        from asgiref.sync import sync_to_async
        from django.db.models import Max
        
        # 获取当前最大的 recording_id 并加1
        from .models import EEGRecord
        try:
            max_record = await sync_to_async(EEGRecord.objects.aggregate)(
                Max('recording_id')
            )
            # 从数据库中获取最大值并加1，如果不存在记录则从1开始
            max_id = max_record['recording_id__max']
            if max_id is not None:
                recording_id = str(int(max_id) + 1)
            else:
                recording_id = '1'
        except Exception as e:
            logger.error(f"获取最大recording_id失败: {str(e)}")
            recording_id = '1'
        
        start_time = timezone.now()
        
        # 使用 sync_to_async 来执行同步的 Django ORM 操作
        record = await sync_to_async(EEGRecord.objects.create)(
            recording_id=recording_id,
            start_time=start_time,
            end_time=start_time,  # 初始结束时间与开始时间相同
            name=name,
            description=description,
            data_count=0
        )
        
        return record

    async def update_eeg_record(self, record):
        """更新EEG记录"""
        from asgiref.sync import sync_to_async
        await sync_to_async(record.save)()

    async def increment_data_count(self, record):
        """增加数据计数"""
        from asgiref.sync import sync_to_async
        await sync_to_async(lambda: setattr(record, 'data_count', record.data_count + 1))()
        await sync_to_async(record.save)()

    async def handle_analysis_request(self, data):
        """处理分析请求"""
        try:
            global current_log_file

            # 验证数据文件
            if not os.path.exists(current_log_file) or os.path.getsize(current_log_file) == 0:
                raise ValueError("无有效数据，请先采集数据")

            # 获取API密钥
            api_key = data.get('api_key', DEFAULT_API_KEY)
            logger.info(f"正在分析数据: {current_log_file}")
            # 执行分析
            analyzer = EEGAnalyzer(current_log_file, api_key)
            report_content, report_path = analyzer.analyze()

            # 分析后轮换日志
            create_new_log_file()

            # 返回结果 
            print(f"分析结果保存在: {report_path}")
            await self.send(text_data=json.dumps({
                'type': 'analysis_result',
                'success': True,
                'content': report_content,
                'path': report_path
            }))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"分析请求失败: {error_msg}")
            await self.send(text_data=json.dumps({
                'type': 'analysis_result',
                'success': False,
                'error': error_msg
            }))
    # async def handle_imported_data(self, data):
    #     """处理导入的数据文件"""
    #     try:
    #         file_path = data.get('filePath', '')
    #         if not file_path or not os.path.exists(file_path):
    #             raise ValueError("导入的文件不存在")
        
    #         global current_log_file
    #         current_log_file = file_path
        
    #         await self.send(text_data=json.dumps({
    #             'type': 'import_success',
    #             'file_path': file_path
    #         }))
        
    #     except Exception as e:
    #         error_msg = str(e)
    #         logger.error(f"导入数据处理失败: {error_msg}")
    #         await self.send(text_data=json.dumps({
    #             'type': 'error',
    #             'message': error_msg
    #         }))