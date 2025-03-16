#!/usr/bin/env python
"""
简化版构建脚本 - 只生成新文章而不影响原网站
"""
import os
import re
import shutil
import markdown
import yaml
from datetime import datetime

# 配置信息
SOURCE_DIR = 'source'
POST_DIR = os.path.join(SOURCE_DIR, '_posts')
PUBLIC_DIR = 'public'
POSTS_OUTPUT_DIR = os.path.join(PUBLIC_DIR, 'posts')

def read_config():
    """读取配置文件"""
    if os.path.exists('config.yml'):
        try:
            with open('config.yml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    return {
        'title': 'My Blog',
        'author': 'Author',
        'description': 'A Cato Blog'
    }

def parse_post(content):
    """解析文章的前置数据和内容"""
    pattern = r'^---\n(.*?)\n---\n(.*)'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            front_matter_str = match.group(1)
            front_matter_str = ''.join(c for c in front_matter_str if c.isprintable())
            front_matter = yaml.safe_load(front_matter_str)
            content = match.group(2).strip()
            return front_matter, content
        except Exception as e:
            print(f"解析前置数据失败: {e}")
            return {}, content
    return {}, content

def normalize_date(date_value):
    """标准化日期格式"""
    if isinstance(date_value, datetime) or isinstance(date_value, str):
        try:
            if isinstance(date_value, str):
                date_value = datetime.strptime(date_value, '%Y-%m-%d')
            return date_value.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"日期格式化错误: {e}")
    return datetime.now().strftime('%Y-%m-%d')

def read_posts():
    """读取所有文章"""
    posts = []
    if not os.path.exists(POST_DIR):
        print(f"文章目录不存在: {POST_DIR}")
        return posts
    
    for filename in os.listdir(POST_DIR):
        if not filename.endswith('.md'):
            continue
        
        try:
            filepath = os.path.join(POST_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            front_matter, content_md = parse_post(content)
            html_content = markdown.markdown(content_md, extensions=['tables', 'fenced_code'])
            
            date_string = normalize_date(front_matter.get('date', datetime.now()))
            
            post = {
                'filename': filename,
                'url': filename.replace('.md', '.html'),
                'content': html_content,
                'date': date_string,
                'title': front_matter.get('title', filename.replace('.md', '')),
                'tags': front_matter.get('tags', []),
                'categories': front_matter.get('categories', []),
                'draft': front_matter.get('draft', False)
            }
            posts.append(post)
        except Exception as e:
            print(f"处理文章时出错 {filename}: {e}")
    
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def ensure_dir(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_posts(posts, config):
    """只生成文章页面"""
    ensure_dir(POSTS_OUTPUT_DIR)
    
    for post in posts:
        if post['draft']:
            continue
            
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{post['title']} - {config.get('title', 'My Blog')}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- 这里不添加任何样式，使用原网站的样式 -->
</head>
<body>
    <article class="post-content">
        <h1>{post['title']}</h1>
        <div class="post-meta">
            <time datetime="{post['date']}">{post['date']}</time>
        </div>
        <div class="post-body">
            {post['content']}
        </div>
    </article>
</body>
</html>
"""
        
        output_file = os.path.join(POSTS_OUTPUT_DIR, post['url'])
        ensure_dir(os.path.dirname(output_file))
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

def generate_index(posts, config):
    """生成文章列表更新首页"""
    ensure_dir(PUBLIC_DIR)
    
    # 只生成一个包含文章列表的HTML片段，而不是完整页面
    posts_html = ""
    for post in posts:
        if post['draft']:
            continue
        posts_html += f"""
        <div class="post-item">
            <h2><a href="posts/{post['url']}">{post['title']}</a></h2>
            <time datetime="{post['date']}">{post['date']}</time>
        </div>
        """
    
    # 简单的首页，只包含文章列表
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{config.get('title', 'My Blog')}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <div class="posts-list">
        {posts_html}
    </div>
</body>
</html>
"""
    
    output_file = os.path.join(PUBLIC_DIR, 'index.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def build_site():
    """构建文章"""
    config = read_config()
    print("读取配置完成")
    
    posts = read_posts()
    print(f"读取文章完成，共 {len(posts)} 篇")
    
    # 确保输出目录存在
    ensure_dir(PUBLIC_DIR)
    
    # 只生成文章页面
    generate_posts(posts, config)
    
    # 更新首页文章列表
    generate_index(posts, config)
    
    print(f"文章生成完成！共 {len(posts)} 篇")

if __name__ == '__main__':
    print("开始生成文章...")
    build_site()
