interface CartFooterProps {
    /** 장바구니 총액 */
    totalAmount: number;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 장바구니 하단 Footer 컴포넌트
 * 장바구니 총액을 우측에 표시
 */
export default function CartFooter({
    totalAmount,
    className = ''
}: CartFooterProps) {
    return (
        <footer
            className={`
        w-full 
        px-6 
        py-4 
        flex 
        items-center 
        justify-end
        ${className}
      `}
            style={{
                backgroundColor: '#667080',
                borderRadius: '30px 30px 0 0',
            }}
        >
            <div className="flex items-center gap-3">
                <span className="text-white text-sm font-medium">
                    Total
                </span>
                <span className="text-white text-2xl font-bold">
                    ${totalAmount.toFixed(2)}
                </span>
            </div>
        </footer>
    );
}
