#!/usr/bin/env python
"""
更新网站CSS样式，确保文章预览正确显示
"""
import os
import re
from bs4 import BeautifulSoup

def update_css_styles(html_file):
    """
    更新HTML文件中的CSS样式，添加文章预览的样式
    """
    if not os.path.exists(html_file):
        print(f"文件不存在: {html_file}")
        return False
    
    try:
        # 读取HTML文件
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找head标签
        head_tag = soup.find('head')
        if not head_tag:
            print("警告: 未找到head标签")
            return False
        
        # 查找是否已有预览样式
        style_tags = soup.find_all('style')
        has_preview_style = False
        for style_tag in style_tags:
            if '.post-preview' in style_tag.text:
                has_preview_style = True
                break
        
        # 如果没有预览样式，添加新的样式
        if not has_preview_style:
            # 创建新的style标签
            new_style = soup.new_tag('style')
            new_style.string = """
/* 文章预览样式 */
.post-preview {
    margin-top: 10px;
    margin-bottom: 20px;
    color: #666;
    font-size: 0.9em;
    line-height: 1.6;
    text-align: justify;
}
.post-item {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
}
.post-title {
    margin-bottom: 10px;
}
"""
            # 添加到head标签
            head_tag.append(new_style)
            
            # 保存修改后的HTML
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            print(f"已更新 {html_file} 的CSS样式")
            return True
        else:
            print(f"{html_file} 已存在预览样式，无需更新")
            return False
    
    except Exception as e:
        print(f"更新CSS样式失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
        update_css_styles(html_file)
    else:
        print("使用方法: python update_styles.py <HTML文件路径>")
