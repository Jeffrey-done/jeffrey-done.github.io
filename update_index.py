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
    - 添加标签导航和RSS链接
    """
    # 读取原始首页
    with open(original_index_path, 'r', encoding='utf-8') as f:
        original_html = f.read()
    
    # 读取新的文章列表
    with open(article_list_path, 'r', encoding='utf-8') as f:
        article_list_html = f.read()
    
    # 解析原始HTML
    soup = BeautifulSoup(original_html, 'html.parser')
    
    # 检查页面是否已经有导航栏
    has_nav = False
    nav_section = soup.find(class_="top-nav")
    if not nav_section:
        nav_section = soup.find("nav")
        if not nav_section or not (
            "返回首页" in nav_section.text or 
            "标签" in nav_section.text or 
            "RSS" in nav_section.text
        ):
            has_nav = False
        else:
            has_nav = True
    else:
        has_nav = True
    
    # 如果没有导航栏，添加一个
    if not has_nav:
        # 添加导航栏样式到head
        head = soup.find('head')
        if head:
            style_tag = soup.new_tag('style')
            style_tag.string = """
            .top-nav {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                padding: 10px 0;
            }
            .top-nav a {
                text-decoration: none;
                color: #666;
            }
            .top-nav a:hover {
                color: #333;
            }
            .tag-list {
                margin: 20px 0;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
                border: 1px solid #eee;
            }
            .tag-list h3 {
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 1.1em;
                color: #555;
            }
            .tag-item {
                display: inline-block;
                background: #f0f0f0;
                padding: 2px 8px;
                margin: 0 5px 5px 0;
                border-radius: 3px;
                font-size: 0.9em;
                color: #666;
                text-decoration: none;
            }
            .tag-item:hover {
                background: #e0e0e0;
            }
            .tag-item.active {
                background: #007bff;
                color: white;
            }
            .post-tags {
                margin-top: 8px;
                font-size: 0.85em;
                color: #777;
            }
            .post-tags a {
                color: #777;
                margin-right: 5px;
                text-decoration: none;
            }
            .post-tags a:hover {
                text-decoration: underline;
            }
            """
            head.append(style_tag)
        
        # 创建导航栏
        nav_div = soup.new_tag('div')
        nav_div['class'] = 'top-nav'
        
        # 添加导航链接
        home_link = soup.new_tag('a')
        home_link['href'] = '#'
        home_link.string = '首页'
        
        tags_link = soup.new_tag('a')
        tags_link['href'] = 'index.html?tag=all'
        tags_link.string = '标签'
        
        rss_link = soup.new_tag('a')
        rss_link['href'] = 'rss.xml'
        rss_link.string = 'RSS'
        
        nav_div.append(home_link)
        nav_div.append(tags_link)
        nav_div.append(rss_link)
        
        # 在body的开始处添加导航栏
        body = soup.find('body')
        if body and body.contents:
            body.insert(0, nav_div)
    
    # 添加标签列表区域
    has_tag_list = soup.find(class_="tag-list")
    if not has_tag_list:
        container = None
        
        # 尝试找到文章列表容器
        content_containers = [
            soup.find(class_='posts'),
            soup.find(class_='post-list'),
            soup.find(class_='articles'),
            soup.find(class_='blog-posts'),
            soup.find(class_='container'),
            soup.find(class_='content'),
            soup.find(id='posts'),
            soup.find(id='post-list'),
            soup.find(id='articles'),
            soup.find(id='blog-posts')
        ]
        
        # 过滤掉None值
        content_containers = [c for c in content_containers if c]
        if content_containers:
            container = content_containers[0]
        else:
            container = soup.find('body')
        
        if container:
            # 创建标签列表区域
            tag_list_div = soup.new_tag('div')
            tag_list_div['class'] = 'tag-list'
            
            # 标签标题
            tag_title = soup.new_tag('h3')
            tag_title.string = '标签云'
            tag_list_div.append(tag_title)
            
            # 从文章列表中提取标签 - 添加一些常用标签作为默认值
            common_tags = ['技术', '生活', '学习', '随笔', '教程']
            for tag in common_tags:
                tag_link = soup.new_tag('a')
                tag_link['href'] = f'index.html?tag={tag}'
                tag_link['class'] = 'tag-item'
                tag_link.string = tag
                tag_list_div.append(tag_link)
                tag_list_div.append(' ')
            
            # 全部标签链接
            all_tag_link = soup.new_tag('a')
            all_tag_link['href'] = 'index.html?tag=all'
            all_tag_link['class'] = 'tag-item'
            all_tag_link.string = '全部'
            tag_list_div.append(all_tag_link)
            
            # 将标签列表插入到文章列表容器之前
            if nav_section:
                nav_section.insert_after(tag_list_div)
            else:
                container.insert(0, tag_list_div)
    
    # 添加JavaScript用于标签筛选
    has_tag_filter_script = False
    scripts = soup.find_all('script')
    for script in scripts:
        if 'filterByTag' in script.text:
            has_tag_filter_script = True
            break
    
    if not has_tag_filter_script:
        script_tag = soup.new_tag('script')
        script_tag.string = """
        // 标签筛选功能
        document.addEventListener('DOMContentLoaded', function() {
            // 解析URL参数
            function getQueryParam(param) {
                var urlParams = new URLSearchParams(window.location.search);
                return urlParams.get(param);
            }
            
            // 获取当前标签
            var currentTag = getQueryParam('tag');
            if (currentTag) {
                filterByTag(currentTag);
                
                // 高亮当前选中的标签
                var tagLinks = document.querySelectorAll('.tag-item');
                tagLinks.forEach(function(link) {
                    if (link.textContent === currentTag || (currentTag === 'all' && link.textContent === '全部')) {
                        link.classList.add('active');
                    }
                });
            }
            
            // 标签筛选
            function filterByTag(tag) {
                var postItems = document.querySelectorAll('.post-item');
                
                if (tag === 'all') {
                    // 显示所有文章
                    postItems.forEach(function(item) {
                        item.style.display = 'block';
                    });
                    return;
                }
                
                postItems.forEach(function(item) {
                    var postTags = item.getAttribute('data-tags');
                    if (postTags && postTags.includes(tag)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
        });
        """
        
        # 添加到body末尾
        body = soup.find('body')
        if body:
            body.append(script_tag)
    
    # 尝试找到文章列表容器
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
    
    # 解析文章列表HTML
    article_soup = BeautifulSoup(article_list_html, 'html.parser')
    article_items = article_soup.find_all(class_='post-item')
    
    # 将文章项目转换为带标签的格式
    for item in article_items:
        # 添加data-tags属性用于JavaScript筛选
        item['data-tags'] = item.get('data-tags', '技术,随笔')
        
        # 如果文章项目没有标签显示，尝试添加一个
        if not item.find(class_='post-tags'):
            # 获取文章标题元素
            title_elem = item.find(class_='post-title')
            if title_elem:
                # 创建标签显示区域
                tags_div = BeautifulSoup('<div class="post-tags">标签: <a href="index.html?tag=技术">技术</a> <a href="index.html?tag=随笔">随笔</a></div>', 'html.parser')
                title_elem.insert_after(tags_div)
    
    # 将处理后的文章列表转回HTML字符串
    processed_article_list_html = ''.join(str(item) for item in article_items)
    
    if article_containers:
        # 使用找到的第一个容器
        container = article_containers[0]
        # 替换内容
        container.clear()
        container.append(BeautifulSoup(processed_article_list_html, 'html.parser'))
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
                updated_html = re.sub(pattern, r'\1' + processed_article_list_html + r'\2', original_html, flags=re.DOTALL)
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
                    parts[middle_index] = processed_article_list_html
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
