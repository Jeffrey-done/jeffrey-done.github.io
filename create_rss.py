#!/usr/bin/env python
"""
生成博客的RSS订阅文件
"""
import os
import re
import sys
from datetime import datetime
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

def clean_html(html_content):
    """清理HTML内容，移除脚本和样式"""
    # 移除script标签及内容
    html_content = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html_content)
    # 移除style标签及内容
    html_content = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html_content)
    return html_content

def extract_preview(html_content, max_length=150):
    """从HTML提取预览文本"""
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', html_content)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 截取预览
    return text[:max_length] + '...' if len(text) > max_length else text

def create_rss(articles_dir, site_url, output_path, site_title="我的博客", site_description="博客文章RSS订阅"):
    """
    创建RSS文件
    
    参数:
        articles_dir: 存放HTML文章的目录
        site_url: 网站URL
        output_path: RSS文件输出路径
        site_title: 网站标题
        site_description: 网站描述
    """
    # 创建RSS根元素，添加必要的命名空间
    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        "xmlns:atom": "http://www.w3.org/2005/Atom"
    })
    channel = ET.SubElement(rss, "channel")
    
    # 添加频道信息
    ET.SubElement(channel, "title").text = site_title
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = site_description
    ET.SubElement(channel, "language").text = "zh-cn"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    
    # 获取所有HTML文章
    articles = []
    for filename in os.listdir(articles_dir):
        if not filename.endswith('.html'):
            continue
        
        try:
            with open(os.path.join(articles_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            title_match = re.search(r'<h1[^>]*class=["\']post-title["\'][^>]*>(.*?)</h1>', content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else filename.replace('.html', '')
            
            # 清理标题中的HTML标签
            title = re.sub(r'<[^>]+>', '', title)
            
            # 提取日期
            date_match = re.search(r'<div[^>]*class=["\']post-meta["\'][^>]*>发布日期:\s*([\d-]+)', content)
            if date_match:
                date_str = date_match.group(1).strip()
                try:
                    pub_date = datetime.strptime(date_str, "%Y-%m-%d")
                    pub_date_rfc = pub_date.strftime("%a, %d %b %Y %H:%M:%S +0800")
                except:
                    pub_date_rfc = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
            else:
                pub_date_rfc = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
            
            # 提取内容
            content_match = re.search(r'<div[^>]*class=["\']post-content["\'][^>]*>(.*?)</div>', content, re.DOTALL)
            post_content = content_match.group(1).strip() if content_match else ""
            
            # 清理内容
            post_content = clean_html(post_content)
            
            # 构建文章链接
            item_link = f"{site_url}/posts/{filename}"
            
            # 提取预览
            description = extract_preview(post_content)
            
            articles.append({
                'title': title,
                'link': item_link,
                'pub_date': pub_date_rfc,
                'description': description,
                'content': post_content
            })
        except Exception as e:
            print(f"处理文章 {filename} 时出错: {e}")
    
    # 按发布日期排序（最新的在前）
    articles.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # 添加文章到RSS
    for article in articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = article['title']
        ET.SubElement(item, "link").text = article['link']
        ET.SubElement(item, "pubDate").text = article['pub_date']
        ET.SubElement(item, "description").text = article['description']
        
        # 添加完整内容（使用CDATA确保HTML标签不被解析）
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = f"<![CDATA[{article['content']}]]>"
    
    # 创建并格式化XML
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # 保存RSS文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"RSS文件生成成功: {output_path}，共 {len(articles)} 篇文章")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python create_rss.py <文章目录> <网站URL> [输出文件路径] [网站标题] [网站描述]")
        sys.exit(1)
    
    articles_dir = sys.argv[1]
    site_url = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else "rss.xml"
    site_title = sys.argv[4] if len(sys.argv) > 4 else "我的博客"
    site_description = sys.argv[5] if len(sys.argv) > 5 else "博客文章RSS订阅"
    
    create_rss(articles_dir, site_url, output_path, site_title, site_description) 
