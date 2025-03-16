#!/usr/bin/env python
"""
处理博客文章和生成文章列表
"""
import os
import re
import yaml
import markdown
from datetime import datetime

# 配置
MD_DIR = 'source/_posts'
HTML_DIR = 'html_articles'

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
        
        with open(master_index, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取head部分，包含所有CSS和meta标签
        head_match = re.search(r'<head>.*?</head>', content, re.DOTALL)
        if not head_match:
            raise ValueError("无法在模板中找到head部分")
        
        head_content = head_match.group(0)
        
        # 寻找在文章列表容器之前的内容作为header模板
        pre_content_parts = content.split('<div class="post-item">')
        if len(pre_content_parts) < 2:
            # 尝试其他可能的分隔点
            for possible_marker in ['<div class="posts">', '<div class="articles">', '<main>', '<article>']:
                if possible_marker in content:
                    pre_content_parts = content.split(possible_marker)
                    break
        
        # 分割后的第一部分作为header模板（但需要去掉head部分，因为我们单独处理它）
        header_template = pre_content_parts[0].replace(head_match.group(0), '')
        
        # 寻找在文章列表容器之后的内容作为footer模板
        post_content_parts = content.split('</div>\n</div>')
        if len(post_content_parts) < 2:
            # 尝试其他可能的结束点
            for possible_end in ['</main>', '</article>', '</body>']:
                if possible_end in content:
                    post_content_parts = content.split(possible_end)
                    if len(post_content_parts) > 1:
                        footer_template = possible_end + post_content_parts[1]
                        return head_content, header_template, footer_template
        
        if len(post_content_parts) > 1:
            footer_template = post_content_parts[1]
            return head_content, header_template, footer_template
        
        # 如果无法提取，返回默认值
        return head_content, "<body>", "</body>"
        
    except Exception as e:
        print(f"提取模板失败: {e}")
        # 返回一个简单的默认模板
        return """<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; line-height: 1.5; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .post-preview { color: #666; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>""", "<body>", "</body>"

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
        print("成功提取主题模板")
    except Exception as e:
        print(f"无法提取主题模板: {e}, 使用默认模板")
        head_template = """<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; line-height: 1.5; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .post-meta { color: #666; margin-bottom: 20px; }
        .post-content { margin-bottom: 30px; }
        .return-link { margin-top: 30px; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>"""
        header_template = """<body>
    <div class="container">"""
        footer_template = """    </div>
</body>
</html>"""
    
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
            
            # 转换为HTML
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            
            # 获取文章信息
            title = frontmatter.get('title', filename.replace('.md', ''))
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
            custom_head = head_template.replace('<title>', f'<title>{title} - ')
            if '<title>' not in head_template:
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
        # 生成文章预览内容
        preview_text = re.sub(r'<[^>]+>', '', article['content'])
        preview_text = preview_text[:150] + '...' if len(preview_text) > 150 else preview_text
        
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
