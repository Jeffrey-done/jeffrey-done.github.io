#!/usr/bin/env python
"""
处理博客文章和生成文章列表
"""
import os
import re
import yaml
import markdown
from datetime import datetime
import shutil

# 配置
MD_DIR = 'source/_posts'
HTML_DIR = 'html_articles'
RESOURCES_DIR = 'resources'  # 用于存储静态资源

def clean_metadata_from_content(content):
    """清理内容中可能存在的元数据字符串"""
    # 移除常见的前置元数据格式
    patterns = [
        r'title:\s+[^\s]+ date:\s+"[^"]+" tags:\s+\[[^\]]*\] author:\s*',
        r'title:\s+[^\s]+ date:\s+"[^"]+" tags:\s+\[[^\]]*\]',
        r'date:\s+"[^"]+" tags:\s+\[[^\]]*\] author:\s*',
        r'title:\s+[^\s]+ date:\s+"[^"]+"',
        r'title:\s+[^\s]+ tags:\s+\[[^\]]*\]',
        r'<p>title:.+?</p>',
        r'<p>date:.+?</p>',
        r'<p>tags:.+?</p>',
        r'<p>author:.+?</p>',
        r'title:.*?\n',
        r'date:.*?\n',
        r'tags:.*?\n',
        r'author:.*?\n',
        r'title:.*? date:.*? tags:.*? author:.*?',
        r'title:.*? date:.*? tags:.*?',
        r'date:.*? tags:.*? author:.*?',
        r'title:.*? date:.*?',
        r'title:.*?date:.*?tags:.*?author:.*?',
        r'title: .+',
        r'date: .+',
        r'tags: .+',
        r'author: .+'
    ]
    
    cleaned_content = content
    for pattern in patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
    
    # 清理其他可能存在的元数据和格式
    cleaned_content = re.sub(r'^---$.*?^---$', '', cleaned_content, flags=re.MULTILINE | re.DOTALL)
    
    return cleaned_content.strip()

def parse_frontmatter(content):
    """解析Markdown文件的前置数据"""
    pattern = r'^---\n(.*?)\n---\n(.*)'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            yaml_str = ''.join(c for c in match.group(1) if c.isprintable())
            frontmatter = yaml.safe_load(yaml_str)
            content = match.group(2).strip()
            return frontmatter, content
        except Exception as e:
            print(f"解析前置数据错误: {e}")
    
    # 如果没有找到前置元数据，检查并移除可能直接写在内容开头的元数据
    content = clean_metadata_from_content(content)
    return {}, content

def extract_template_from_master():
    """
    尝试从master分支的index.html提取头部和尾部模板
    如果master分支不存在，返回简单的默认模板
    """
    try:
        # 如果在自动部署中，master分支内容位于这个路径
        master_index = 'master-website/index.html'
        if not os.path.exists(master_index):
            # 检查本地的情况
            master_index = '../master/index.html'
            if not os.path.exists(master_index):
                raise FileNotFoundError("找不到主题模板文件")
        
        # 复制CSS和其他资源文件
        master_dir = os.path.dirname(master_index)
        if not os.path.exists(RESOURCES_DIR):
            os.makedirs(RESOURCES_DIR)
            
        # 复制css目录
        css_dir = os.path.join(master_dir, 'css')
        if os.path.exists(css_dir):
            if not os.path.exists(os.path.join(RESOURCES_DIR, 'css')):
                shutil.copytree(css_dir, os.path.join(RESOURCES_DIR, 'css'))
                print(f"已复制CSS资源到{RESOURCES_DIR}/css")
        
        # 复制js目录
        js_dir = os.path.join(master_dir, 'js')
        if os.path.exists(js_dir):
            if not os.path.exists(os.path.join(RESOURCES_DIR, 'js')):
                shutil.copytree(js_dir, os.path.join(RESOURCES_DIR, 'js'))
                print(f"已复制JS资源到{RESOURCES_DIR}/js")
                
        # 复制图片目录
        for img_dir in ['images', 'img', 'assets']:
            src_img_dir = os.path.join(master_dir, img_dir)
            if os.path.exists(src_img_dir):
                if not os.path.exists(os.path.join(RESOURCES_DIR, img_dir)):
                    shutil.copytree(src_img_dir, os.path.join(RESOURCES_DIR, img_dir))
                    print(f"已复制图片资源到{RESOURCES_DIR}/{img_dir}")
        
        with open(master_index, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取head部分，包含所有CSS和meta标签
        head_match = re.search(r'<head.*?>.*?</head>', content, re.DOTALL)
        if not head_match:
            raise ValueError("无法在模板中找到head部分")
        
        head_content = head_match.group(0)
        
        # 更新资源路径
        head_content = re.sub(r'(href|src)="(?!http)(.*?)(\.css|\.js)"', r'\1="../\2\3"', head_content)
        head_content = re.sub(r'(href|src)="(?!http)(images|img|assets)/(.*?)"', r'\1="../\2/\3"', head_content)
        
        # 寻找在文章列表容器之前的内容作为header模板
        pre_content_parts = content.split('<div class="post-item">')
        if len(pre_content_parts) < 2:
            # 尝试其他可能的分隔点
            for possible_marker in ['<div class="posts">', '<div class="articles">', '<main>', '<article>', '<div class="container">']:
                if possible_marker in content:
                    pre_content_parts = content.split(possible_marker)
                    break
        
        # 分割后的第一部分作为header模板（但需要去掉head部分，因为我们单独处理它）
        header_template = pre_content_parts[0].replace(head_match.group(0), '')
        
        # 寻找在文章列表容器之后的内容作为footer模板
        post_content_parts = content.split('</div>\n</div>')
        if len(post_content_parts) < 2:
            # 尝试其他可能的结束点
            for possible_end in ['</main>', '</article>', '</body>', '</div>']:
                if possible_end in content:
                    post_content_parts = content.split(possible_end)
                    if len(post_content_parts) > 1:
                        footer_template = possible_end + post_content_parts[1]
                        break
            else:
                footer_template = "</body></html>"
        else:
            footer_template = post_content_parts[1]
        
        # 更新资源路径
        header_template = re.sub(r'(href|src)="(?!http)(.*?)(\.css|\.js)"', r'\1="../\2\3"', header_template)
        header_template = re.sub(r'(href|src)="(?!http)(images|img|assets)/(.*?)"', r'\1="../\2/\3"', header_template)
        
        footer_template = re.sub(r'(href|src)="(?!http)(.*?)(\.css|\.js)"', r'\1="../\2\3"', footer_template)
        footer_template = re.sub(r'(href|src)="(?!http)(images|img|assets)/(.*?)"', r'\1="../\2/\3"', footer_template)
        
        print("成功提取主题模板")
        return head_content, header_template, footer_template
        
    except Exception as e:
        print(f"提取模板失败: {e}")
        # 返回一个简单但美观的默认模板
        return """<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            color: #333;
            background-color: #f8f9fa;
        }
        h1 { 
            color: #212529; 
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 0.5rem;
        }
        h2, h3, h4, h5, h6 {
            color: #343a40;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .post-meta { 
            color: #6c757d; 
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        .post-content { 
            background-color: #fff;
            padding: 2rem;
            border-radius: 5px;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            margin-bottom: 2rem;
        }
        .return-link { 
            margin-top: 2rem;
            text-align: center;
        }
        a { 
            color: #007bff; 
            text-decoration: none; 
        }
        a:hover { 
            text-decoration: underline; 
            color: #0056b3;
        }
        pre, code {
            background-color: #f1f3f5;
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        pre {
            padding: 1rem;
            overflow-x: auto;
        }
        pre code {
            padding: 0;
            background-color: transparent;
        }
        blockquote {
            border-left: 4px solid #ced4da;
            margin-left: 0;
            padding-left: 1rem;
            color: #6c757d;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1rem auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        th, td {
            padding: 0.5rem;
            border: 1px solid #dee2e6;
        }
        th {
            background-color: #e9ecef;
        }
    </style>
</head>""", """<body>
    <div class="container">""", """    </div>
</body>
</html>"""

def generate_articles():
    """生成文章HTML文件和文章列表"""
    if not os.path.exists(HTML_DIR):
        os.makedirs(HTML_DIR)
    
    if not os.path.exists(MD_DIR):
        print(f"文章目录不存在: {MD_DIR}")
        return []
    
    # 尝试提取主题模板
    try:
        head_template, header_template, footer_template = extract_template_from_master()
    except Exception as e:
        print(f"无法提取主题模板: {e}, 使用默认模板")
        head_template = """<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            color: #333;
            background-color: #f8f9fa;
        }
        h1 { 
            color: #212529; 
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 0.5rem;
        }
        h2, h3, h4, h5, h6 {
            color: #343a40;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .post-meta { 
            color: #6c757d; 
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        .post-content { 
            background-color: #fff;
            padding: 2rem;
            border-radius: 5px;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            margin-bottom: 2rem;
        }
        .return-link { 
            margin-top: 2rem;
            text-align: center;
        }
        a { 
            color: #007bff; 
            text-decoration: none; 
        }
        a:hover { 
            text-decoration: underline; 
            color: #0056b3;
        }
        pre, code {
            background-color: #f1f3f5;
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        pre {
            padding: 1rem;
            overflow-x: auto;
        }
        pre code {
            padding: 0;
            background-color: transparent;
        }
        blockquote {
            border-left: 4px solid #ced4da;
            margin-left: 0;
            padding-left: 1rem;
            color: #6c757d;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1rem auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        th, td {
            padding: 0.5rem;
            border: 1px solid #dee2e6;
        }
        th {
            background-color: #e9ecef;
        }
    </style>
</head>"""
        header_template = """<body>
    <div class="container">"""
        footer_template = """    </div>
</body>
</html>"""
    
    # 确保资源目录存在
    if not os.path.exists(os.path.join(HTML_DIR, 'resources')):
        if os.path.exists(RESOURCES_DIR):
            shutil.copytree(RESOURCES_DIR, os.path.join(HTML_DIR, 'resources'))
    
    articles = []
    
    for filename in os.listdir(MD_DIR):
        if not filename.endswith('.md'):
            continue
        
        input_path = os.path.join(MD_DIR, filename)
        output_path = os.path.join(HTML_DIR, filename.replace('.md', '.html'))
        
        try:
            # 读取Markdown内容
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 解析前置数据
            frontmatter, content = parse_frontmatter(md_content)
            
            # 确保内容中没有元数据字符串
            content = clean_metadata_from_content(content)
            
            # 转换为HTML前清理Markdown源码中的元数据
            content = clean_metadata_from_content(content)
            
            # 移除Markdown源码中的HTML标签
            content = re.sub(r'<[^>]+>', '', content)
            
            # 分析文件内容，尝试提取第一个标题作为备用标题
            first_heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            backup_title = first_heading_match.group(1).strip() if first_heading_match else None
            
            # 转换为HTML
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            
            # 再次清理可能残留在内容中的元数据文本
            html_content = clean_metadata_from_content(html_content)
            
            # 移除可能的HTML中的元数据段落
            html_content = re.sub(r'<p>title:.*?</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p>date:.*?</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p>tags:.*?</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p>author:.*?</p>', '', html_content, flags=re.IGNORECASE)
            
            # 自动识别可能的元数据段落（开头的几行含有冒号的文本）并移除
            lines = html_content.split('\n')
            clean_lines = []
            skip_mode = True  # 初始默认跳过开头的元数据
            
            for line in lines:
                # 如果是可能的元数据行（含有冒号且在文档开头），跳过
                if skip_mode and re.search(r'<p>[^:]+:.+</p>', line):
                    continue
                else:
                    # 一旦遇到非元数据行，停止跳过模式
                    skip_mode = False
                    clean_lines.append(line)
            
            html_content = '\n'.join(clean_lines)
            
            # 获取文章信息 - 优先使用frontmatter中的标题
            title = None
            
            # 1. 首先尝试从frontmatter中获取标题
            if frontmatter and 'title' in frontmatter and frontmatter['title']:
                title = frontmatter['title']
            
            # 2. 如果frontmatter中没有标题，尝试使用第一个Markdown标题作为标题
            if not title and backup_title:
                title = backup_title
            
            # 3. 如果以上都不存在，才使用文件名
            if not title:
                title = filename.replace('.md', '')
            
            # 获取日期信息
            date_str = frontmatter.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # 尝试解析日期以便排序
            try:
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    date_obj = date_str
                date_formatted = date_obj.strftime('%Y-%m-%d')
            except:
                date_formatted = str(date_str)
                date_obj = datetime.now()  # 默认值用于排序
            
            # 添加到文章列表
            articles.append({
                'title': title,
                'date': date_formatted,
                'date_obj': date_obj,
                'filename': filename.replace('.md', '.html'),
                'content': html_content
            })
            
            # 生成带主题的文章HTML
            # 修改<head>中的标题
            custom_head = head_template
            if '<title>' in custom_head:
                custom_head = custom_head.replace('<title>', f'<title>{title} - ')
            else:
                custom_head = custom_head.replace('</head>', f'<title>{title}</title></head>')
            
            html = f"""<!DOCTYPE html>
<html>
{custom_head}
{header_template}
    <article class="post">
        <h1 class="post-title">{title}</h1>
        <div class="post-meta">发布日期: {date_formatted}</div>
        <div class="post-content">
            {html_content}
        </div>
        <div class="return-link">
            <a href="../index.html">返回首页</a>
        </div>
    </article>
{footer_template}"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"生成文章: {filename} -> {os.path.basename(output_path)}")
        
        except Exception as e:
            print(f"处理文章失败 {filename}: {e}")
    
    # 按日期排序文章
    articles.sort(key=lambda x: x['date_obj'], reverse=True)
    
    # 生成文章列表HTML片段
    article_list_html = ""
    for article in articles:
        # 生成文章预览内容 - 去除所有HTML标签和多余空白
        raw_content = re.sub(r'<[^>]+>', '', article['content'])
        # 删除任何剩余的元数据文本
        raw_content = clean_metadata_from_content(raw_content)
        # 移除Markdown格式如 #, *, -, ```等
        raw_content = re.sub(r'[#*`\-_]+', '', raw_content)
        # 替换连续多个空白为单个空格
        raw_content = re.sub(r'\s+', ' ', raw_content).strip()
        # 截取预览文本
        preview_text = raw_content[:150] + '...' if len(raw_content) > 150 else raw_content
        
        # 使用更简洁的HTML格式，只显示标题和预览内容
        article_list_html += f"""
<div class="post-item">
    <h2 class="post-title"><a href="posts/{article['filename']}">{article['title']}</a></h2>
    <div class="post-preview">{preview_text}</div>
</div>
"""
    
    # 保存文章列表HTML片段
    with open(os.path.join(HTML_DIR, 'article_list.html'), 'w', encoding='utf-8') as f:
        f.write(article_list_html)
    
    print(f"生成文章列表，共 {len(articles)} 篇文章")
    return articles

if __name__ == "__main__":
    print("开始处理博客文章...")
    generate_articles()
    print("处理完成！") 
