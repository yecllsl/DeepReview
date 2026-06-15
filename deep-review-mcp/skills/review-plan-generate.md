---
name: review-plan-generate
description: 复习计划生成流程编排
triggers:
  - command: /review
  - keywords: ["复习计划", "复习推荐", "该复习什么"]
---

# 复习计划生成流程

1. **获取到期错题**：调用 `recommend_review`
2. **展示概览**：到期数量、薄弱知识点排名
3. **展示每日计划**：按日期展示复习清单
4. **用户确认**：确认或调整
5. **保存计划**

遗忘曲线间隔：1天→3天→7天→14天→30天
