main :: IO ()
main = putStrLn answer

expectedValue :: Double
expectedValue = sum [1 - (1 - 0.5 ** fromIntegral n) ** 32 | n <- [0..200]]

answer :: String
answer = take 12 (show expectedValue)
