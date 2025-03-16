#!/usr/bin/env python
"""
智能更新首页，只替换文章列表部分
"""
import re
import sys
from bs4 import BeautifulSoup

def update_index_page(original_index_path, article_list_path, output_path):
    """
    智能更新首页
    - 保持原始的HTML结构和样式
    - 只更新文章列表部分
    """
    # 读取原始首页
    with open(original_index_path, 'r', encoding='utf-8') as f:
        original_html = f.read()
    
    # 读取新的文章列表
    with open(article_list_path, 'r', encoding='utf-8') as f:
        article_list_html = f.read()
    
    # 解析原始HTML
    soup = BeautifulSoup(original_html, 'html.parser')
    
    # 尝试找到文章列表容器
    # 常见的文章列表容器类名
    article_containers = [
        soup.find(class_='posts'),
        soup.find(class_='post-list'),
        soup.find(class_='articles'),
        soup.find(class_='blog-posts'),
        soup.find(id='posts'),
        soup.find(id='post-list'),
        soup.find(id='articles'),
        soup.find(id='blog-posts')
    ]
    
    # 过滤掉None值
    article_containers = [c for c in article_containers if c]
    
    if article_containers:
        # 使用找到的第一个容器
        container = article_containers[0]
        # 替换内容
        container.clear()
        container.append(BeautifulSoup(article_list_html, 'html.parser'))
        updated_html = str(soup)
        print(f"成功找到文章列表容器: {container.name}{'#'+container['id'] if container.has_attr('id') else ''}{'.'+container['class'][0] if container.has_attr('class') else ''}")
    else:
        # 如果找不到明确的容器，使用正则表达式
        # 尝试匹配常见的文章列表模式
        patterns = [
            r'(<div\s+class=["\']post[s]?(?:-list)?["\'][^>]*>).*?(</div>)',
            r'(<div\s+class=["\']articles?["\'][^>]*>).*?(</div>)',
            r'(<div\s+class=["\']blog-posts?["\'][^>]*>).*?(</div>)',
            r'(<div\s+id=["\']post[s]?(?:-list)?["\'][^>]*>).*?(</div>)',
            r'(<div\s+id=["\']articles?["\'][^>]*>).*?(</div>)',
            r'(<main[^>]*>).*?(</main>)',
            r'(<article[^>]*>).*?(</article>)'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, original_html, re.DOTALL):
                updated_html = re.sub(pattern, r'\1' + article_list_html + r'\2', original_html, flags=re.DOTALL)
                updated = True
                print(f"使用正则表达式更新文章列表")
                break
        
        if not updated:
            # 如果所有尝试都失败，只替换<body>标签内容，但保持结构
            body_pattern = r'(<body[^>]*>)(.*)(</body>)'
            if re.search(body_pattern, original_html, re.DOTALL):
                body_match = re.search(body_pattern, original_html, re.DOTALL)
                body_content = body_match.group(2)
                
                # 将body内容分为上下两部分
                # 假设文章列表位于中间部分
                parts = re.split(r'(<div[^>]*>.*?</div>)', body_content, flags=re.DOTALL)
                if len(parts) >= 3:
                    # 更新中间部分
                    middle_index = len(parts) // 2
                    parts[middle_index] = article_list_html
                    new_body = ''.join(parts)
                    updated_html = re.sub(body_pattern, r'\1' + new_body + r'\3', original_html, flags=re.DOTALL)
                    print("无法找到明确的文章容器，尝试更新正文中间部分")
                else:
                    # 如果分割失败，只能添加新内容但不替换
                    updated_html = original_html
                    print("警告：无法识别文章列表位置，将原样保留首页")
            else:
                updated_html = original_html
                print("警告：无法找到body标签，将原样保留首页")
    
    # 保存更新后的首页
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    print(f"首页更新完成: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用方法: python update_index.py 原始首页路径 文章列表路径 输出路径")
        sys.exit(1)
    
    original_index_path = sys.argv[1]
    article_list_path = sys.argv[2]
    output_path = sys.argv[3]
    
    update_index_page(original_index_path, article_list_path, output_path) 
