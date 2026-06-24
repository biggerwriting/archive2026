import { storage } from '../../utils/storage'
import { BADGE_DEFS } from '../../utils/constants'

Page({
  data: { badges: [], earned: 0, total: BADGE_DEFS.length },

  async onShow() {
    const earnedArr = (await storage.get('badges')) || []
    const earnedMap = new Map(earnedArr.map(b => [b.id, b.earnedAt]))
    const badges = BADGE_DEFS.map(def => {
      const at = earnedMap.get(def.id)
      const d  = at ? new Date(at) : null
      return {
        ...def,
        earned:  !!at,
        dateStr: d ? `${d.getMonth()+1}月${d.getDate()}日 获得` : '',
      }
    })
    this.setData({ badges, earned: earnedArr.length })
  },
})
