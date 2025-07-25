# 个人随笔博客系统

这是一个简单而优雅的博客系统，专为发布个人随笔和思考而设计。

## 如何添加新的博客文章

### 1. 创建新的 Markdown 文件

在 `blog/posts/` 目录下创建新的 `.md` 文件，文件名格式：`YYYY-MM-DD-title.md`

例如：`2024-03-15-my-thoughts-on-learning.md`

### 2. 使用标准的文章模板

每篇文章都应该包含以下 YAML 前置元数据：

```markdown
---
title: "文章标题"
date: "YYYY-MM-DD"
category: "分类名称"
tags: ["标签1", "标签2", "标签3"]
excerpt: "文章摘要，简短描述文章内容"
---

# 文章标题

在这里写你的文章内容...

## 小标题

文章内容...

---

*写作时间和地点（可选）*
```

### 3. 更新博客索引

在 `blog/index.html` 文件中，找到 `blogPosts` 数组，添加新文章的信息：

```javascript
const blogPosts = [
    {
        title: "你的文章标题",
        date: "2024-03-15",
        category: "分类名称",
        excerpt: "文章摘要",
        filename: "2024-03-15-your-article-filename.md"
    },
    // 其他文章...
];
```

### 4. 更新文章内容

在 `blog/post.html` 文件中，找到 `mockPosts` 对象，添加新文章的完整内容：

```javascript
const mockPosts = {
    '2024-03-15-your-article-filename.md': {
        title: '你的文章标题',
        date: '2024-03-15',
        category: '分类名称',
        content: `# 你的文章标题

在这里粘贴你的完整 Markdown 内容...`
    },
    // 其他文章...
};
```

## 文章分类建议

- **技术思考** - 关于技术、编程、AI 等的思考
- **生活感悟** - 日常生活的感悟和思考
- **学习笔记** - 学习过程中的记录和总结
- **读书心得** - 读书后的感想和收获
- **旅行随想** - 旅行中的见闻和思考

## 写作建议

1. **保持真实性** - 写出真实的想法和感受
2. **结构清晰** - 使用标题和段落来组织内容
3. **简洁明了** - 避免冗长的句子，保持表达清晰
4. **个人化** - 加入个人的经历和观点
5. **定期更新** - 保持写作的习惯

## 技术特性

- 响应式设计，支持移动端访问
- 优雅的动画效果和交互
- 支持中英文双语切换
- 简洁美观的卡片式布局
- 平滑的页面滚动和导航

---

*享受写作的过程，记录思考的轨迹！* ✍️
