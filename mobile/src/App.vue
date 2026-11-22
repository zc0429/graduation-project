<script>
export default {}
</script>

<style>
page {
  background: #f2f5f7;
  color: #172b3a;
  font-size: 30rpx;
  line-height: 1.55;
}
.screen {
  box-sizing: border-box;
  min-height: 100vh;
  padding: 28rpx 28rpx 48rpx;
}
.card {
  box-sizing: border-box;
  min-width: 0;
  margin-bottom: 20rpx;
  padding: 26rpx;
  border: 1px solid #e0e7eb;
  border-radius: 18rpx;
  background: #fff;
}
.title, .heading, .label, .copy { display: block; overflow-wrap: anywhere; }
.title { margin-bottom: 14rpx; font-size: 42rpx; font-weight: 700; }
.heading { margin-bottom: 12rpx; font-size: 32rpx; font-weight: 650; }
.label { margin: 22rpx 0 8rpx; font-weight: 600; }
.copy { white-space: pre-wrap; word-break: break-word; }
.muted { color: #4e6070; font-size: 27rpx; }
.error { display: block; margin: 12rpx 0; color: #a01f2d; }
.field {
  box-sizing: border-box;
  width: 100%;
  min-height: 84rpx;
  padding: 16rpx;
  border: 1px solid #bbc9cf;
  border-radius: 10rpx;
  background: #fff;
  font-size: 30rpx;
  line-height: 1.5;
}
textarea.field { height: 210rpx; }
button.action, .action-link {
  box-sizing: border-box;
  display: block;
  width: 100%;
  min-height: 82rpx;
  margin: 16rpx 0 0;
  padding: 15rpx 20rpx;
  border: 1px solid #bccbc9;
  border-radius: 10rpx;
  background: #fff;
  color: #155c50;
  text-align: center;
  font-size: 30rpx;
  line-height: 1.55;
  overflow-wrap: anywhere;
}
button.action::after { border: 0; }
button.primary, .action-link.primary { background: #155c50; color: #fff; border-color: #155c50; }
button.action[disabled] { opacity: .62; }
.link-card { display: block; }
.meta { margin-bottom: 10rpx; display: flex; flex-wrap: wrap; gap: 6rpx 18rpx; }
.preview { display: block; width: 100%; margin-top: 16rpx; }
</style>
