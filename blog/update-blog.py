#!/usr/bin/env python3
"""
博客内容更新脚本
用于自动读取markdown文件并更新HTML中的静态数据
"""
import os
import re
import json
from datetime import datetime

def parse_front_matter(content):
    """解析Markdown文件的front matter"""
    if not content.startswith('---'):
        return {}, content
    
    try:
        end_pos = content.find('---', 3)
        if end_pos == -1:
            return {}, content
        
        front_matter = content[3:end_pos].strip()
        markdown_content = content[end_pos + 3:].strip()
        
        metadata = {}
        for line in front_matter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                metadata[key] = value
        
        return metadata, markdown_content
    except:
        return {}, content

def read_markdown_files():
    """读取所有markdown文件"""
    posts_dir = 'posts'
    blog_posts = []
    articles = {}
    
    if not os.path.exists(posts_dir):
        print(f"错误：{posts_dir} 目录不存在")
        return [], {}
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(posts_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata, markdown_content = parse_front_matter(content)
                
                # 为博客列表准备数据
                post_data = {
                    'title': metadata.get('title', '无标题'),
                    'date': metadata.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'category': metadata.get('category', '未分类'),
                    'excerpt': metadata.get('excerpt', '暂无摘要'),
                    'filename': filename
                }
                blog_posts.append(post_data)
                
                # 为文章内容准备数据
                articles[filename] = {
                    'title': post_data['title'],
                    'date': post_data['date'],
                    'category': post_data['category'],
                    'content': markdown_content
                }
                
                print(f"✓ 读取文件: {filename}")
                
            except Exception as e:
                print(f"✗ 读取文件 {filename} 失败: {e}")
    
    # 按日期排序
    blog_posts.sort(key=lambda x: x['date'], reverse=True)
    
    return blog_posts, articles

def update_index_html(blog_posts):
    """更新index.html文件"""
    index_file = 'index.html'
    
    if not os.path.exists(index_file):
        print(f"错误：{index_file} 文件不存在")
        return
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成JavaScript数组
        js_array = "        const blogPosts = [\n"
        for post in blog_posts:
            js_array += f"""            {{
                title: "{post['title']}",
                date: "{post['date']}",
                category: "{post['category']}",
                excerpt: "{post['excerpt']}",
                filename: "{post['filename']}"
            }},\n"""
        js_array += "        ];"
        
        # 替换现有的blogPosts数组
        pattern = r'const blogPosts = \[[\s\S]*?\];'
        new_content = re.sub(pattern, js_array, content)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ 更新 {index_file}")
        
    except Exception as e:
        print(f"✗ 更新 {index_file} 失败: {e}")

def update_post_html(articles):
    """更新post.html文件"""
    post_file = 'post.html'
    
    if not os.path.exists(post_file):
        print(f"错误：{post_file} 文件不存在")
        return
    
    try:
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成JavaScript对象
        js_object = "        const articles = {\n"
        for filename, article in articles.items():
            # 转义内容中的反引号和特殊字符
            escaped_content = article['content'].replace('`', '\\`').replace('${', '\\${')
            js_object += f"""            "{filename}": {{
                title: "{article['title']}",
                date: "{article['date']}",
                category: "{article['category']}",
                content: `{escaped_content}`
            }},\n"""
        js_object += "        };"
        
        # 替换现有的articles对象
        pattern = r'const articles = \{[\s\S]*?\};'
        new_content = re.sub(pattern, js_object, content)
        
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ 更新 {post_file}")
        
    except Exception as e:
        print(f"✗ 更新 {post_file} 失败: {e}")

def main():
    print("🔄 开始更新博客...")
    
    # 读取markdown文件
    blog_posts, articles = read_markdown_files()
    
    if not blog_posts:
        print("❌ 没有找到任何markdown文件")
        return
    
    print(f"📚 找到 {len(blog_posts)} 篇文章")
    
    # 更新HTML文件
    update_index_html(blog_posts)
    update_post_html(articles)
    
    print("✅ 博客更新完成！")
    print("\n📋 文章列表:")
    for post in blog_posts:
        print(f"  • {post['title']} ({post['date']})")

if __name__ == '__main__':
    main()
