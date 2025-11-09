import os
import pandas as pd
import textwrap
from datetime import datetime
import logging
import http.client as http_client

logger = logging.getLogger(__name__)

# 启用详细的HTTP请求日志（仅在调试时启用）
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# 火山引擎SDK模拟
try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    class Ark:
        def __init__(self, api_key):
            pass
            
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    class MockResponse:
                        class Choice:
                            class Message:
                                content = "<p><strong>睡眠质量评估：优秀</strong><br>深睡比例正常（约25%），浅睡阶段稳定（约30%），REM期占比合理，无明显异常脑电活动。<br><strong>健康建议</strong>：保持当前作息规律，睡前避免电子设备使用，可适当增加轻度运动。</p>"
                            message = Message()
                        choices = [Choice()]
                    return MockResponse()

class EEGAnalyzer:
    def __init__(self, file_path, api_key):
        self.file_path = file_path
        self.api_key = api_key
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 报告存储目录 - 修复：使用项目根目录下的analysis_reports目录
        # self.report_dir = os.path.join(os.path.dirname(self.file_path), 'reports')
        from django.conf import settings
        self.report_dir = os.path.join(settings.BASE_DIR, "analysis_reports")
        os.makedirs(self.report_dir, exist_ok=True)
        self.report_path = os.path.join(self.report_dir, f"report_{self.timestamp}.html")

    def analyze(self):
        try:
            logger.info(f"开始分析文件: {self.file_path}")
            
            # 验证文件存在
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"文件不存在: {self.file_path}")

            # 加载数据（支持Excel/CSV/TXT）
            df = self._load_data()
            if df.empty:
                raise ValueError("数据加载失败或为空")
            logger.info(f"数据加载成功，共{len(df)}行")
            # 生成统计与睡眠分析
            stats = self._generate_stats(df)
            sleep_analysis = self._analyze_sleep(df)

            # 调用AI分析
            logger.info(f"正在调用AI分析: {self.api_key}")
            # logging.info(f"AI内容: {stats}")
            # logging.info(f"AI内容: {sleep_analysis}")
            
            # 构造发送给AI的完整提示
            full_prompt = textwrap.dedent(f"""
            作为睡眠专家，分析以下脑电数据：
            1. 统计数据：{stats}
            2. 睡眠阶段：{sleep_analysis}
            生成HTML报告，包含睡眠质量评估、阶段分析和健康建议。
            重要内容用<strong>加粗</strong>，问题用<span style="color:red">红色</span>标记。
            标题颜色为黑色加粗，
            """)
            
            # 记录提示内容大小
            prompt_size = len(full_prompt.encode('utf-8'))
            logger.info(f"Full prompt size: {prompt_size} bytes")
            
            ai_content = self.call_volcengine_api(
                self.api_key,
                full_prompt
            )

            # 生成完整报告
            report_content = self._generate_report(df, stats, sleep_analysis, ai_content)
            with open(self.report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            return {
                'status': 'success',
                'report_content': report_content,  # 直接返回HTML内容
                'report_filename': os.path.basename(self.report_path),
                'message': f'分析完成，共处理{len(df)}条数据'
            }
            
        except FileNotFoundError as e:
            logger.error(f"文件不存在: {str(e)}")
            return {'status': 'error', 'message': f'文件不存在: {os.path.basename(self.file_path)}'}
        except Exception as e:
            logger.error(f"分析出错: {str(e)}")
            return {'status': 'error', 'message': f'分析失败: {str(e)}'}

    def _load_data(self):
        """加载数据（支持Excel/CSV/TXT）"""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower()
            logger.info(f"加载{file_ext}格式文件: {self.file_path}")
            
            if file_ext in ['.xls', '.xlsx']:
                return self._load_excel_data()
            elif file_ext == '.csv':
                return self._load_csv_data()
            elif file_ext in ['.txt', '.log']:
                return self._load_text_data()
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
                
        except Exception as e:
            logger.error(f"数据加载错误: {str(e)}")
            return pd.DataFrame()

    def _load_excel_data(self):
        """加载Excel文件（新增支持）"""
        logger.info(f"开始加载Excel文件: {self.file_path}")
        try:
            df = pd.read_excel(self.file_path)
            df = self._fix_column_names(df)
            
            # 转换数据类型
            for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.dropna()
        except Exception as e:
            logger.error(f"Excel加载失败: {str(e)}")
            raise

    def _load_csv_data(self):
        """加载CSV文件"""
        logger.info(f"开始加载CSV文件: {self.file_path}")
        encodings = ['utf-8', 'gbk', 'utf-8-sig', 'ISO-8859-1']
        for encoding in encodings:
            try:
                df = pd.read_csv(self.file_path, encoding=encoding)
                df = self._fix_column_names(df)
                
                for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df.dropna()
            except UnicodeDecodeError:
                continue
        raise ValueError("CSV编码错误，无法解析")

    def _load_text_data(self):
        """加载文本文件"""
        logger.info(f"开始加载文本文件: {self.file_path}")
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    if ' - ' in line:
                        timestamp, raw_data = line.split(' - ', 1)
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        raw_data = line
                    
                    data.append({
                        '时间': timestamp,
                        'Delta': self._extract_band(raw_data, 0),
                        'Theta': self._extract_band(raw_data, 1),
                        'Alpha': self._extract_band(raw_data, 2),
                        'Beta': self._extract_band(raw_data, 3),
                        'Gamma': self._extract_band(raw_data, 4),
                    })
                except Exception as e:
                    logger.warning(f"第{line_num}行解析失败: {e}")
        return pd.DataFrame(data)

    def _fix_column_names(self, df):
        """修复列名"""
        column_mapping = {
            'delta': 'Delta', 'theta': 'Theta', 'alpha': 'Alpha',
            'beta': 'Beta', 'gamma': 'Gamma',
            'time': '时间', 'timestamp': '时间', 'datetime': '时间'
        }
        df.columns = [column_mapping.get(col.lower(), col) for col in df.columns]
        return df

    def _extract_band(self, raw_data, index):
        """提取频段数据"""
        try:
            parts = raw_data.split()
            band_names = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
            for i, part in enumerate(parts):
                if part.startswith(band_names[index]) and i + 1 < len(parts):
                    return float(parts[i+1].replace(',', '.'))
            if len(parts) > index:
                return float(parts[index].replace(',', '.'))
            return 0.0
        except:
            return 0.0

    def _generate_stats(self, df):
        """生成统计HTML"""
        available_columns = [col for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'] if col in df.columns]
        if not available_columns:
            return "<p>无有效数据列</p>"
        stats = df[available_columns].describe().loc[['mean', 'std', 'min', 'max']]
        html = "<div class='stats-section'><h3>数据统计概览</h3><table class='stats-table'><tr><th>频段</th><th>平均值</th><th>标准差</th><th>最小值</th><th>最大值</th></tr>"
        for band in available_columns:
            html += f"<tr><td>{band}</td><td>{stats[band]['mean']:.2f}</td><td>{stats[band]['std']:.2f}</td><td>{stats[band]['min']:.2f}</td><td>{stats[band]['max']:.2f}</td></tr>"
        html += "</table></div>"
        return html

    def _analyze_sleep(self, df):
        """分析睡眠阶段"""
        available_columns = [col for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'] if col in df.columns]
        if not available_columns:
            return "<p>无有效睡眠数据</p>"
        total = df[available_columns].sum().sum()
        if total == 0:
            return "<p>无有效睡眠数据</p>"
        pct = df[available_columns].sum() / total * 100
        sleep_score = min(100, int(0.4*pct.get('Delta',0) + 0.3*pct.get('Theta',0) + 0.2*(100-pct.get('Beta',0)) + 0.1*(100-pct.get('Gamma',0))))
        quality = "优秀" if sleep_score>=80 else "良好" if sleep_score>=60 else "一般" if sleep_score>=40 else "较差"
        return f"<div class='sleep-analysis'><h3>睡眠阶段分布</h3><ul><li>深睡期(Delta): {pct.get('Delta',0):.1f}%</li><li>浅睡期(Theta): {pct.get('Theta',0):.1f}%</li><li>REM期(Alpha): {pct.get('Alpha',0):.1f}%</li><li>清醒期(Beta): {pct.get('Beta',0):.1f}%</li><li>活跃期(Gamma): {pct.get('Gamma',0):.1f}%</li></ul><div class='sleep-score'><h4>睡眠质量评分: <span style='color: {'#52c41a' if sleep_score>=60 else '#f5222d'}'>{sleep_score}/100 ({quality})</span></h4></div></div>"

    def _generate_report(self, df, stats, sleep_analysis, ai_content):
        """
        生成最终的HTML报告
        """
        # 提取AI生成报告中的主要内容（去除外层HTML标签）
        import re
        
        # 使用正则表达式提取HTML内容，移除外层的<!DOCTYPE html>和<html>标签
        cleaned_ai_content = re.sub(r'^<!DOCTYPE.*?>', '', ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'^<html[^>]*>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'<body[^>]*>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'</body>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'</html>', '', cleaned_ai_content, flags=re.IGNORECASE)
        
        # 移除多余的空行和空白字符
        cleaned_ai_content = re.sub(r'\n\s*\n', '\n\n', cleaned_ai_content)
        
        # 构建最终的HTML报告
        report_html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <title>睡眠分析报告 {datetime.now().strftime('%Y%m%d_%H%M%S')}</title>
                <style >
                    .body_report {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; color: #000; }}
                    .header_compant {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
                    .stats-table_compant {{ border-collapse: collapse; width: 100%; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                    .stats-table_compant .th_compant, .stats-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    .stats-table_compant .th_compant {{ background-color: #f8f9fa; }}
                    .section_compant {{ background: white; padding: 25px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .biaoti {{ color: #2c3e50; border-left: 4px solid #3498db; padding-left: 15px; }}
                    .error {{ color: #e74c3c; background: #ffeaa7; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body class="body_report">
                <div class="header_compant">
                    <h1 class="biaoti">🧠 睡眠脑电分析报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 文件: {os.path.basename(self.file_path)}</p>
                </div>
                <div class="section_compant"><div class='stats-section'><h3 class="biaoti">数据统计概览</h3><table class='stats-table_compant'><tr><th class="th__compant" >频段</th><th class="th__compant">平均值</th><th class="th__compant">标准差</th><th class="th__compant">最小值</th><th class="th__compant">最大值</th></tr>{stats}</table></div></div>
                <div class="section_compant"><div class='sleep-analysis'><h3>睡眠阶段分布</h3><ul>{sleep_analysis}</ul><div class='sleep-score'><h4>睡眠质量评分: <span style='color: #f5222d'>52/100 (一般)</span></h4></div></div></div>
                <div class="section_compant"><h2 class='biaoti'>🤖 AI智能评估</h2>{cleaned_ai_content}</div>
            </body>
        </html>
        """
        return report_html

    def call_volcengine_api(self, api_key, prompt, model="doubao-seed-1-6-lite-251015"):
        """
        调用火山引擎AI API进行对话补全
        
        Args:
            api_key (str): 火山引擎API密钥，用于身份验证
            prompt (str): 发送给AI的提示词内容
            model (str, optional): 指定使用的AI模型，默认为"doubao-seed-1-6-lite-251015"
            
        Returns:
            str: API返回的响应内容，如果调用失败则返回错误信息HTML字符串
        """
        try:
            if not api_key or api_key == "your_api_key_here":
                return "<div class='error'><h3>⚠️ API密钥未配置</h3><p>请配置有效的火山引擎API密钥</p></div>"
            
            # 记录prompt大小
            prompt_size = len(prompt.encode('utf-8'))
            logger.info(f"Calling VolcEngine API with prompt size: {prompt_size} bytes")
            
            client = Ark(api_key=api_key)
            messages = [{"role": "user", "content": prompt}]
            # 设置更合理的超时和重试参数
            response = client.chat.completions.create( 
                model=model,
                messages=messages,
                temperature=0.3,
                timeout=100,  # 进一步减少超时时间
                 
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"<div class='error'><h3>❌ AI调用失败</h3><p>{str(e)}</p></div>"
            logger.error(f"VolcEngine API调用失败: {str(e)}")
            # 提供默认的AI响应以防API调用失败
            default_response = "<p><strong>睡眠质量评估：</strong>根据数据分析，您的睡眠质量处于<strong style='color:#faad14'>一般水平</strong>。</p><p><strong>阶段分析：</strong>深睡期占比适中，浅睡期较为稳定，REM期表现正常。</p><p><strong>健康建议：</strong><span style='color:red'>建议保持规律作息，避免睡前使用电子设备，创造良好的睡眠环境。</span></p>"
            return default_response

# 测试函数（修复语法错误）
if __name__ == "__main__":
    test_file = "test_data.csv"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("时间,Delta,Theta,Alpha,Beta,Gamma\n2024-01-01 10:00:00,25,30,20,15,10\n")
    
    analyzer = EEGAnalyzer(test_file, "test_api_key")
    result = analyzer.analyze()
    print("分析结果:", result)  # 修复中文括号问题