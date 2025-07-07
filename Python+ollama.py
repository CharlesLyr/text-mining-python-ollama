import os
import pdfplumber
import pandas as pd
import requests
from tqdm import tqdm
import time


class PDFAnalyzer:
    def __init__(self, ollama_url="http://localhost:11434", model="deepseek-r1:1.5b", timeout=120):
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        self.max_text_length = 8000  # 添加最大文本长度限制

    def extract_text_from_pdf(self, pdf_path):
        """提取PDF文件的前三页内容"""
        print("正在提取PDF前三页文本...")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    print("PDF为空")
                    return None

                text = ""
                max_pages = min(3, len(pdf.pages))  # 最多提取3页，若页数不足则提取全部
                for i in range(max_pages):
                    page_text = pdf.pages[i].extract_text() or ""
                    text += page_text + "\n"

                text = text.strip()

                if len(text) > self.max_text_length:
                    print(f"警告：文本长度（{len(text)}字符）超过限制，将截取前{self.max_text_length}字符进行分析")
                    text = text[:self.max_text_length]
                else:
                    print(f"成功提取前三页文本，长度：{len(text)}字符")

                return text
        except Exception as e:
            print(f"PDF提取错误: {e}")
            return None

    def check_ollama_status(self):
        """检查Ollama服务状态"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def call_ollama(self, prompt):
        """调用 Ollama API（旧接口 /api/generate）"""
        print("正在调用AI分析...")

        if not self.check_ollama_status():
            print("错误：无法连接到Ollama服务，请确保服务正在运行")
            return None

        try:
            start_time = time.time()
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,  #
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=self.timeout
            )

            print(f"API响应时间：{time.time() - start_time:.2f}秒")

            if response.status_code != 200:
                print(f"API错误：状态码 {response.status_code}")
                print(f"错误信息：{response.text}")
                return None

            result = response.json()
            full_response = result.get("response", "[无返回内容]")

            # 提取 </think> 之后的内容（若存在）
            if "</think>" in full_response:
                cleaned = full_response.split("</think>")[-1].strip()
                if cleaned:
                    return cleaned

            # 否则返回完整内容
            return full_response.strip()

        except requests.exceptions.Timeout:
            print(f"请求超时（{self.timeout}秒）")
            return None
        except Exception as e:
            print(f"API调用错误: {e}")
            if 'response' in locals():
                print(f"API响应: {response.text}")
            return None

    def analyze_research_method(self, text):
        """分析研究方法"""
        if not text:
            print("错误：没有文本内容可分析")
            return None

        prompt = """总结这篇文章运用了什么研究方法，在以下类别中只能选择一个回答：量化研究、质性研究、理论研究、政策研究、综述研究。



文章内容：
{text}"""

        return self.call_ollama(prompt.format(text=text))

    def process_single_pdf(self, pdf_path, output_file="research_method.csv"):
        """处理单个PDF文件"""
        print(f"\n开始处理文件: {pdf_path}")

        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            print("错误：文件不存在")
            return False

        # 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("文本提取失败")
            return False

        # 分析文本
        analysis = self.analyze_research_method(text)
        if not analysis:
            print("分析失败")
            return False

        # 保存结果
        pd.DataFrame([{
            'filename': os.path.basename(pdf_path),
            'research_method': analysis
        }]).to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"结果已保存至: {output_file}")
        return True

    def process_pdf_directory(self, directory_path = r"E:\xxx" , output_file="research_methods.csv"):
        """处理目录中的所有PDF文件并生成CSV报告"""
        if not os.path.exists(directory_path):
            print(f"错误：目录不存在 - {directory_path}")
            return

        pdf_files = [f for f in os.listdir(directory_path) if f.endswith('.pdf')]

        if not pdf_files:
            print(f"警告：在目录 {directory_path} 中没有找到PDF文件")
            return

        print(f"找到 {len(pdf_files)} 个PDF文件")
        results = []

        for pdf_file in tqdm(pdf_files, desc="处理PDF文件"):
            pdf_path = os.path.join(directory_path, pdf_file)
            print(f"\n开始处理: {pdf_file}")

            text = self.extract_text_from_pdf(pdf_path)
            if text:
                analysis = self.analyze_research_method(text)
                if analysis:
                    results.append({
                        'filename': pdf_file,
                        'research_method': analysis
                    })
                    print(f"成功分析文件: {pdf_file}")
                else:
                    print(f"无法获取文件 {pdf_file} 的分析结果")
            else:
                print(f"无法提取文件 {pdf_file} 的文本内容")

        if results:
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n处理完成！分析结果已保存到: {output_file}")
            print(f"成功处理 {len(results)}/{len(pdf_files)} 个文件")
        else:
            print("\n没有成功处理任何PDF文件")


if __name__ == "__main__":
    analyzer = PDFAnalyzer(timeout=120)

    # 设置要处理的目录
    directory_path = r"E:\xxx"

    # 输出的分析结果 CSV（原始）
    raw_output_csv = "research_methods.csv"

    # 输出的清洗结果 CSV
    cleaned_output_csv = "research_methods_cleaned.csv"

    analyzer.process_pdf_directory(directory_path=directory_path, output_file=raw_output_csv)

    def clean_research_methods(input_csv, output_csv):
        df = pd.read_csv(input_csv)

        allowed_methods = ["量化研究", "质性研究", "理论研究", "政策研究", "综述研究",
                           "定量研究", "定性研究"]

        def extract_methods(text):
            if not isinstance(text, str):
                return ""
            found = set()
            for method in allowed_methods:
                if method in text:
                    found.add(method)
            return "、".join(sorted(found)) if found else "未识别"

        df['cleaned_method'] = df['research_method'].apply(extract_methods)
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\n 清洗完成，结果已保存到：{output_csv}")
        print(df[['filename', 'cleaned_method']].head())


    clean_research_methods(input_csv=raw_output_csv, output_csv=cleaned_output_csv)
