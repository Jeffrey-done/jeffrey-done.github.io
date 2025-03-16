#!/usr/bin/env python
"""
独立博客构建脚本 - 不依赖cato包的安装
直接将Markdown文件转换为HTML并部署
"""
import os
import re
import shutil
import markdown
import yaml
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# 配置信息
SOURCE_DIR = 'source'
POST_DIR = os.path.join(SOURCE_DIR, '_posts')
TEMPLATE_DIR = os.path.join(SOURCE_DIR, '_templates')
ASSET_DIR = os.path.join(SOURCE_DIR, 'assets')
PUBLIC_DIR = 'public'

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
        'description': 'A Cato Blog',
        'theme': 'default',
        'url': 'https://example.com'
    }

def parse_post(content):
    """解析文章的前置数据和内容"""
    pattern = r'^---\n(.*?)\n---\n(.*)'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            # 使用安全的方式解析YAML，处理特殊字符
            front_matter_str = match.group(1)
            # 先过滤掉不可见的特殊字符
            front_matter_str = ''.join(c for c in front_matter_str if c.isprintable())
            front_matter = yaml.safe_load(front_matter_str)
            content = match.group(2).strip()
            return front_matter, content
        except Exception as e:
            print(f"解析前置数据失败: {e}")
            # 返回一个基本的前置数据
            return {}, content
    return {}, content

def normalize_date(date_value):
    """标准化日期格式"""
    if isinstance(date_value, datetime) or isinstance(date_value, str):
        try:
            if isinstance(date_value, str):
                # 尝试将字符串转换为日期对象
                date_value = datetime.strptime(date_value, '%Y-%m-%d')
            # 返回ISO格式的日期字符串
            return date_value.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"日期格式化错误: {e}")
    # 默认返回今天的日期
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
            
            # 确保日期是一个标准化的字符串格式
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
    
    # 按日期排序 - 确保所有日期都是字符串类型，可以直接比较
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def clear_directory(directory):
    """清空目录"""
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

def copy_assets():
    """复制静态资源"""
    if os.path.exists(ASSET_DIR):
        target_dir = os.path.join(PUBLIC_DIR, 'assets')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        for item in os.listdir(ASSET_DIR):
            source = os.path.join(ASSET_DIR, item)
            destination = os.path.join(target_dir, item)
            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)

def build_site():
    """构建整个站点"""
    config = read_config()
    print("读取配置完成")
    
    posts = read_posts()
    print(f"读取文章完成，共 {len(posts)} 篇")
    
    # 创建输出目录
    clear_directory(PUBLIC_DIR)
    print("已清空输出目录")
    
    # 设置模板引擎
    theme = config.get('theme', 'default')
    template_path = os.path.join(TEMPLATE_DIR, 'themes', theme)
    if not os.path.exists(template_path):
        print(f"主题不存在: {theme}，使用默认主题")
        template_path = os.path.join(TEMPLATE_DIR, 'themes', 'default')
        if not os.path.exists(template_path):
            print("默认主题也不存在，创建简单主题")
            os.makedirs(template_path, exist_ok=True)
            with open(os.path.join(template_path, 'post.html'), 'w', encoding='utf-8') as f:
                f.write(DEFAULT_POST_TEMPLATE)
            with open(os.path.join(template_path, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(DEFAULT_INDEX_TEMPLATE)
    
    try:
        env = Environment(loader=FileSystemLoader(template_path))
        
        # 生成文章页面
        for post in posts:
            if post['draft']:
                continue
            
            try:
                template = env.get_template('post.html')
                html = template.render(post=post, config=config, posts=posts)
                
                output_file = os.path.join(PUBLIC_DIR, post['url'])
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html)
            except Exception as e:
                print(f"生成文章页面失败: {post['filename']} - {e}")
        
        # 生成首页
        try:
            template = env.get_template('index.html')
            html = template.render(posts=posts, config=config)
            
            output_file = os.path.join(PUBLIC_DIR, 'index.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as e:
            print(f"生成首页失败: {e}")
            # 创建一个简单的首页
            create_simple_index(posts, config)
    except Exception as e:
        print(f"设置模板引擎失败: {e}")
        # 完全回退到简单模式
        create_simple_index(posts, config)
        create_simple_posts(posts, config)
    
    # 复制静态资源
    copy_assets()
    
    print(f"构建完成！生成了 {len(posts)} 篇文章")

def create_simple_posts(posts, config):
    """创建简单的文章页面"""
    for post in posts:
        if post['draft']:
            continue
            
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{post['title']} - {config.get('title', 'My Blog')}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .post-date {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .post-content {{ margin-top: 30px; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ font-family: Consolas, Monaco, 'Andale Mono', monospace; }}
    </style>
</head>
<body>
    <header>
        <h1>{post['title']}</h1>
        <div class="post-date">{post['date']}</div>
    </header>
    <div class="post-content">
        {post['content']}
    </div>
    <footer>
        <p><a href="index.html">← 返回首页</a></p>
        <p>&copy; {config.get('author', 'Author')}. All rights reserved.</p>
    </footer>
</body>
</html>
"""
        
        output_file = os.path.join(PUBLIC_DIR, post['url'])
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

def create_simple_index(posts, config):
    """创建简单的首页"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{config.get('title', 'My Blog')}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .post {{ margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        .post h2 {{ margin-bottom: 10px; }}
        .post-date {{ color: #666; font-size: 0.9em; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <h1>{config.get('title', 'My Blog')}</h1>
        <p>{config.get('description', '')}</p>
    </header>
    <main>
"""
    
    for post in posts:
        if post['draft']:
            continue
        html += f"""
        <div class="post">
            <h2><a href="{post['url']}">{post['title']}</a></h2>
            <div class="post-date">{post['date']}</div>
        </div>
"""
    
    html += f"""
    </main>
    <footer>
        <p>&copy; {datetime.now().year} {config.get('author', 'Author')}. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    
    output_file = os.path.join(PUBLIC_DIR, 'index.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

# 默认模板
DEFAULT_POST_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ post.title }} - {{ config.title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .post-date { color: #666; font-size: 0.9em; margin-bottom: 20px; }
        .post-content { margin-top: 30px; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { font-family: Consolas, Monaco, 'Andale Mono', monospace; }
    </style>
</head>
<body>
    <header>
        <h1>{{ post.title }}</h1>
        <div class="post-date">{{ post.date }}</div>
    </header>
    <div class="post-content">
        {{ post.content|safe }}
    </div>
    <footer>
        <p><a href="index.html">← 返回首页</a></p>
        <p>&copy; {{ config.author }}. All rights reserved.</p>
    </footer>
</body>
</html>
"""

DEFAULT_INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ config.title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .post { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        .post h2 { margin-bottom: 10px; }
        .post-date { color: #666; font-size: 0.9em; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <header>
        <h1>{{ config.title }}</h1>
        <p>{{ config.description }}</p>
    </header>
    <main>
        {% for post in posts %}
        {% if not post.draft %}
        <div class="post">
            <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
            <div class="post-date">{{ post.date }}</div>
        </div>
        {% endif %}
        {% endfor %}
    </main>
    <footer>
        <p>&copy; {{ config.author }}. All rights reserved.</p>
    </footer>
</body>
</html>
"""

if __name__ == '__main__':
    print("开始构建博客...")
    build_site()
