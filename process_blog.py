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

def generate_articles():
    """生成文章HTML文件和文章列表"""
    if not os.path.exists(HTML_DIR):
        os.makedirs(HTML_DIR)
    
    if not os.path.exists(MD_DIR):
        print(f"文章目录不存在: {MD_DIR}")
        return []
    
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
            
            # 生成文章HTML
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <article>
        <h1>{title}</h1>
        <div>发布日期: {date_formatted}</div>
        <div>
            {html_content}
        </div>
        <div>
            <a href="../index.html">返回首页</a>
        </div>
    </article>
</body>
</html>"""
            
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
